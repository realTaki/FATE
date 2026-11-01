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
package com.webank.ai.fate.core;

import com.webank.ai.fate.core.constant.StatusCode;
import com.webank.ai.fate.core.utils.Configuration;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.XML;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import static org.junit.Assert.*;

/** Offline, temporary-file configuration and bounded parser regressions. */
public class JsonConfigurationSecurityTest {
    @Rule
    public TemporaryFolder directory = new TemporaryFolder();

    @Test
    public void actualConfigurationPreservesUtf8AndOrdinaryJsonValues() throws Exception {
        File base = directory.newFile("base.properties");
        Files.write(base.toPath(), "json.security.synthetic=value\n".getBytes(StandardCharsets.UTF_8));
        File adapters = directory.newFolder("adapter_conf");
        File fixture = new File(adapters, "normal.json");
        String text = "{\"label\":\"配置 \\u2603\",\"enabled\":true,\"count\":7,"
                + "\"fraction\":1.25,\"items\":[\"first\",2,null],\"nested\":{\"ok\":true}}";
        Files.write(fixture.toPath(), text.getBytes(StandardCharsets.UTF_8));
        Configuration configuration = new Configuration(base.getAbsolutePath());
        assertEquals(StatusCode.OK, configuration.load());
        assertEquals("value", Configuration.getProperty("json.security.synthetic"));
        JSONObject parsed = Configuration.getAdapterJsonConfig("normal.json");
        assertNotNull(parsed);
        assertEquals("配置 \u2603", parsed.getString("label"));
        assertTrue(parsed.getBoolean("enabled"));
        assertEquals(7, parsed.getInt("count"));
        assertEquals(1.25, parsed.getDouble("fraction"), 0.0);
        assertEquals(3, parsed.getJSONArray("items").length());
        assertTrue(parsed.getJSONArray("items").isNull(2));
        JSONObject roundTrip = new JSONObject(parsed.toString());
        assertTrue(roundTrip.getJSONObject("nested").getBoolean("ok"));
        assertEquals("first", roundTrip.getJSONArray("items").getString(0));
    }

    @Test
    public void actualConfigurationRetainsMalformedJsonErrorStatus() throws Exception {
        File base = directory.newFile("base.properties");
        File adapters = directory.newFolder("adapter_conf");
        Files.write(new File(adapters, "invalid.json").toPath(),
                "{\"broken\":".getBytes(StandardCharsets.UTF_8));
        assertEquals(StatusCode.UNKNOWNERROR, new Configuration(base.getAbsolutePath()).load());
    }

    @Test
    public void embeddedNulDoesNotBecomeAnEscapingObjectKey() {
        // Small, fixed fixture from the CVE-2023-5072 parser condition;
        // never create the large exponential-memory proof of concept.
        String nested = "{\"a\":1}";
        for (int i = 0; i < 3; i++) {
            nested = "{\"a\":1;\t\0" + nested + ":1}";
        }
        String[] inputs = {"{\"myKey\":true, \0\"myOtherKey\":false}", nested};
        for (String input : inputs) {
            try {
                new JSONObject(input);
                fail("Expected embedded-NUL parser rejection");
            } catch (JSONException expected) {
                assertNotNull(expected.getMessage());
            }
        }
    }

    @Test
    public void xmlDepthLimitReturnsAParserError() {
        // Library-only CVE-2022-45688 boundary; no XML use was found in Configuration.
        // Fixed input <8 KiB, far below memory-exhaustion payload sizes.
        StringBuilder xml = new StringBuilder(7200);
        for (int i = 0; i < 1024; i++) xml.append("<n>");
        xml.append("synthetic");
        for (int i = 0; i < 1024; i++) xml.append("</n>");
        try {
            XML.toJSONObject(xml.toString());
            fail("Expected the library XML nesting limit");
        } catch (JSONException expected) {
            assertNotNull(expected.getMessage());
        }
    }
}
