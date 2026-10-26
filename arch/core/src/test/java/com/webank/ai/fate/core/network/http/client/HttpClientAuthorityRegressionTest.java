/*
 * Copyright 2026 The FATE Authors. All Rights Reserved.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.webank.ai.fate.core.network.http.client;

import com.sun.net.httpserver.HttpServer;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.UnknownHostException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.http.HttpException;
import org.apache.http.HttpHost;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URIUtils;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.junit.Test;
import static org.junit.Assert.*;

/** Regression for GHSA-7r82-7xv7-xcpj / CVE-2020-13956.
 * Malformed authority shapes follow Apache's e628b4c fix. No external DNS,
 * credentials, production requests, or TLS trust changes are used here.
 */
public class HttpClientAuthorityRegressionTest {
    private static final String[] AMBIGUOUS = {
        "http://127.0.0.1:8080;sessionid=fixture/abcd",
        "http://127.0.0.1:;sessionid=fixture/abcd",
        "http://synthetic@first.invalid:80@second.invalid/"
    };

    @Test(timeout = 2000)
    public void malformedAuthoritiesDoNotProduceATarget() throws Exception {
        for (String value : AMBIGUOUS) {
            assertNull(value, URIUtils.extractHost(new URI(value)));
        }
    }

    @Test(timeout = 2000)
    public void normalAuthoritiesKeepTheirHostPortAndScheme() throws Exception {
        assertEquals(new HttpHost("127.0.0.1", 8080),
            URIUtils.extractHost(new URI("http://127.0.0.1:8080/;sessionid=fixture/abcd")));
        assertEquals(new HttpHost("example.invalid", 8443, "https"),
            URIUtils.extractHost(new URI("https://synthetic@example.invalid:8443/a?q=b#c")));
        assertEquals(new HttpHost("[::1]", 8080),
            URIUtils.extractHost(new URI("http://[::1]:8080/a")));
        assertNull(URIUtils.extractHost(new URI("/relative/path")));
    }

    @Test(timeout = 2000)
    public void ambiguousRequestsAreRejectedBeforeAnyRouteOrNetwork() throws Exception {
        final AtomicInteger routes = new AtomicInteger();
        try (CloseableHttpClient client = HttpClients.custom()
                .disableAutomaticRetries()
                .setRoutePlanner((host, request, context) -> {
                    routes.incrementAndGet();
                    throw new HttpException("test guard: network is forbidden");
                }).build()) {
            for (String value : AMBIGUOUS) {
                try {
                    client.execute(new HttpGet(new URI(value))).close();
                    fail("malformed authority was accepted");
                } catch (ClientProtocolException expected) {
                    // A patched client rejects the URI before route planning.
                    assertEquals(value, 0, routes.get());
                }
            }
        }
    }

    private static CloseableHttpClient loopbackClient() {
        return HttpClients.custom().disableAutomaticRetries()
            .setDefaultRequestConfig(RequestConfig.custom()
                .setConnectionRequestTimeout(500).setConnectTimeout(500)
                .setSocketTimeout(500).build())
            .setDnsResolver(host -> {
                if (!"127.0.0.1".equals(host)) {
                    throw new UnknownHostException("test forbids external DNS: " + host);
                }
                return new InetAddress[] {InetAddress.getByAddress(new byte[] {127, 0, 0, 1})};
            }).build();
    }

    private static HttpServer server(AtomicInteger requests) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/echo", exchange -> {
            requests.incrementAndGet();
            ByteArrayOutputStream body = new ByteArrayOutputStream();
            try (InputStream input = exchange.getRequestBody()) {
                byte[] buffer = new byte[256];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    body.write(buffer, 0, count);
                }
            }
            String value = exchange.getRequestMethod() + "|" + exchange.getRequestURI()
                + "|" + new String(body.toByteArray(), StandardCharsets.UTF_8);
            byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
            // Keep this minimal fixture independent of HTTP keep-alive timing.
            exchange.getResponseHeaders().set("Connection", "close");
            exchange.sendResponseHeaders(200, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        });
        server.createContext("/redirect", exchange -> {
            requests.incrementAndGet();
            exchange.getRequestBody().close();
            exchange.getResponseHeaders().set("Connection", "close");
            exchange.getResponseHeaders().set("Location", "/echo?redirected=1");
            exchange.sendResponseHeaders(302, -1);
            exchange.close();
        });
        server.start();
        return server;
    }

    @Test(timeout = 4000)
    public void loopbackGetAndJsonPostPreserveMethodPathAndBody() throws Exception {
        AtomicInteger requests = new AtomicInteger();
        HttpServer server = server(requests);
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        try (CloseableHttpClient client = loopbackClient()) {
            try (CloseableHttpResponse response = client.execute(new HttpGet(base + "/echo?q=a%20b"))) {
                assertEquals(200, response.getStatusLine().getStatusCode());
                assertEquals("GET|/echo?q=a%20b|", EntityUtils.toString(response.getEntity(), "UTF-8"));
            }
            HttpPost post = new HttpPost(base + "/echo");
            post.setHeader("Content-Type", "application/json;charset=UTF-8");
            post.setEntity(new StringEntity("{\"fixture\":1}", "UTF-8"));
            try (CloseableHttpResponse response = client.execute(post)) {
                assertEquals(200, response.getStatusLine().getStatusCode());
                assertEquals("POST|/echo|{\"fixture\":1}", EntityUtils.toString(response.getEntity(), "UTF-8"));
            }
            assertEquals(2, requests.get());
        } finally {
            server.stop(0);
        }
    }

    @Test(timeout = 4000)
    public void loopbackSameOriginRedirectKeepsWorking() throws Exception {
        AtomicInteger requests = new AtomicInteger();
        HttpServer server = server(requests);
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        try (CloseableHttpClient client = loopbackClient();
             CloseableHttpResponse response = client.execute(new HttpGet(base + "/redirect"))) {
            assertEquals(200, response.getStatusLine().getStatusCode());
            assertEquals("GET|/echo?redirected=1|", EntityUtils.toString(response.getEntity(), "UTF-8"));
            assertEquals(2, requests.get());
        } finally {
            server.stop(0);
        }
    }
}
