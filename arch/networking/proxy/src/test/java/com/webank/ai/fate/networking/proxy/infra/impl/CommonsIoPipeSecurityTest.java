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
package com.webank.ai.fate.networking.proxy.infra.impl;

import com.google.protobuf.ByteString;
import com.webank.ai.fate.api.networking.proxy.Proxy;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.io.IOUtils;
import org.apache.commons.io.input.XmlStreamReader;
import org.junit.Test;
import static org.junit.Assert.*;

/** Synthetic in-memory stream controls and finite library security boundaries. */
public class CommonsIoPipeSecurityTest {
    @Test
    public void actualInputPipePreservesPayloadAndQuietClose() {
        final int[] closes = {0};
        byte[] payload = "synthetic-input".getBytes(StandardCharsets.UTF_8);
        ByteArrayInputStream input = new ByteArrayInputStream(payload) {
            @Override public void close() throws IOException {
                closes[0]++;
                throw new IOException("synthetic close failure");
            }
        };
        InputStreamToPacketUnidirectionalPipe pipe = new InputStreamToPacketUnidirectionalPipe(
                input, Proxy.Metadata.getDefaultInstance(), 64);
        assertArrayEquals(payload, pipe.read().getBody().getValue().toByteArray());
        assertNull(pipe.read());
        pipe.close();
        assertEquals(1, closes[0]);
        assertTrue(pipe.isClosed());
        assertTrue(pipe.isDrained());
    }

    @Test
    public void actualOutputPipePreservesPayloadAndSuppressesCloseFailure() {
        final int[] calls = {0, 0};
        ByteArrayOutputStream output = new ByteArrayOutputStream() {
            @Override public void flush() throws IOException {
                calls[0]++;
                throw new IOException("synthetic flush failure");
            }
            @Override public void close() throws IOException {
                calls[1]++;
                throw new IOException("synthetic close failure");
            }
        };
        byte[] payload = "synthetic-output".getBytes(StandardCharsets.UTF_8);
        PacketToOutputStreamUnidirectionalPipe pipe = new PacketToOutputStreamUnidirectionalPipe(output);
        pipe.write(Proxy.Packet.newBuilder().setBody(
                Proxy.Data.newBuilder().setValue(ByteString.copyFrom(payload))).build());
        assertArrayEquals(payload, output.toByteArray());
        pipe.close();
        assertEquals(1, calls[0]);
        assertEquals(1, calls[1]);
        assertTrue(pipe.isClosed());
    }

    @Test
    public void ordinaryXmlEncodingAndPathControlsArePreserved() throws Exception {
        String xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><root>配置</root>";
        try (XmlStreamReader reader = new XmlStreamReader(
                new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)))) {
            assertEquals("UTF-8", reader.getEncoding());
            assertEquals(xml, IOUtils.toString(reader));
        }
        assertEquals("base/file.bin", FilenameUtils.normalize("base/sub/../file.bin", true));
    }

    @Test
    public void invalidUncParentPrefixesAreRejected() {
        assertNull(FilenameUtils.normalize("//../synthetic"));
        assertNull(FilenameUtils.normalize("\\\\..\\synthetic"));
    }

    @Test
    public void malformedXmlPrologRegexStaysWithinFiniteWorkBudget() {
        StringBuilder input = new StringBuilder(800);
        for (int i = 0; i < 128; i++) input.append("<?xml ");
        input.append('>');
        // The library uses this same public pattern in XmlStreamReader.
        // Count character accesses instead of running an unbounded CPU/timing PoC.
        WorkCounter counter = new WorkCounter();
        assertFalse(XmlStreamReader.ENCODING_PATTERN.matcher(
                new BudgetSequence(input.toString(), counter)).find());
        assertTrue(counter.reads <= 8192);
    }

    private static final class WorkCounter { private int reads; }

    private static final class BudgetSequence implements CharSequence {
        private final String value;
        private final WorkCounter counter;
        private BudgetSequence(String value, WorkCounter counter) {
            this.value = value;
            this.counter = counter;
        }
        @Override public int length() { return value.length(); }
        @Override public char charAt(int index) {
            if (++counter.reads > 8192) {
                throw new IllegalStateException("XML prolog regex exceeded finite character budget");
            }
            return value.charAt(index);
        }
        @Override public CharSequence subSequence(int start, int end) {
            return new BudgetSequence(value.substring(start, end), counter);
        }
        @Override public String toString() { return value; }
    }
}
