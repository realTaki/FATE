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

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.core.LoggerContext;
import org.apache.logging.log4j.core.impl.Log4jLogEvent;
import org.apache.logging.log4j.core.layout.PatternLayout;
import org.apache.logging.log4j.message.MapMessage;
import org.apache.logging.log4j.message.SimpleMessage;
import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** Logging-only regression tests: no service, network, model or data access. */
public class Log4jSecurityTest {
    @Test
    public void apiAndCoreVersionsAreAligned() {
        String api = LogManager.class.getPackage().getImplementationVersion();
        String core = LoggerContext.class.getPackage().getImplementationVersion();
        assertNotNull(api);
        assertEquals("2.25.5", api);
        assertEquals(api, core);
    }

    @Test
    public void messageLookupSyntaxIsNotExpanded() {
        String literal = "untrusted ${java:version}";
        String rendered = PatternLayout.newBuilder().withPattern("%m").build()
                .toSerializable(Log4jLogEvent.newBuilder()
                        .setMessage(new SimpleMessage(literal)).build());
        assertEquals(literal, rendered);
    }

    @Test
    public void nonFiniteMapValuesAreQuotedInJson() {
        for (double value : new double[] {
                Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY}) {
            Map<String, Object> values = new HashMap<>();
            values.put("value", value);
            MapMessage<?, ?> message = new MapMessage<>(values);
            String json = message.getFormattedMessage(new String[] {"JSON"});
            // RFC 8259 forbids bare NaN/Infinity numeric tokens (CVE-2026-49844).
            assertTrue(json, json.contains("\"" + Double.toString(value) + "\""));
            assertEquals("{\"value\":\"" + Double.toString(value) + "\"}", json);
        }
    }

    @Test
    public void finiteMapValuesRemainJsonNumbers() {
        Map<String, Object> values = new HashMap<>();
        values.put("value", 1.5d);
        String json = new MapMessage<>(values)
                .getFormattedMessage(new String[] {"JSON"});
        assertEquals("{\"value\":1.5}", json);
    }
}
