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

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.deser.DefaultDeserializationContext;
import com.fasterxml.jackson.databind.exc.InvalidTypeIdException;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.databind.jsontype.TypeDeserializer;
import com.fasterxml.jackson.databind.jsontype.impl.TypeDeserializerBase;
import com.webank.ai.fate.core.bean.ReturnResult;
import com.webank.ai.fate.core.serdes.impl.GeneralJsonBytesSerDes;
import com.webank.ai.fate.core.serdes.impl.GeneralJsonStringSerDes;
import com.webank.ai.fate.core.utils.ObjectTransform;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.Test;
import static org.junit.Assert.*;

/** Actual project JSON APIs and finite inert library regressions, not an exploit chain. */
public class JacksonFamilySecurityTest {
    @JsonPropertyOrder({"name", "count", "optional"})
    public static class Sample {
        public String name;
        public int count;
        public String optional;
    }
    private Sample sample() {
        Sample value = new Sample(); value.name = "FATE-测试"; value.count = 7; return value;
    }
    private String golden() {
        return "[\"" + Sample.class.getName() + "\",{\"name\":\"FATE-测试\",\"count\":7}]";
    }
    @Test public void actualStringSerDesKeepsTypedWireAndNormalContracts() {
        GeneralJsonStringSerDes serdes = new GeneralJsonStringSerDes();
        assertEquals(golden(), serdes.serialize(sample()));
        Sample parsed = serdes.deserialize(golden(), Sample.class);
        assertEquals("FATE-测试", parsed.name); assertEquals(7, parsed.count); assertNull(parsed.optional);
        String withComment = golden().replace("{", "{/*finite*/").replace("\"count\":7", "\"count\":7,\"unknown\":true");
        assertEquals(7, serdes.deserialize(withComment, Sample.class).count);
        assertNull(serdes.serialize(null)); assertNull(serdes.deserialize(null, Sample.class));
    }
    @Test public void actualBytesSerDesKeepsUtf8AndTypedWire() {
        GeneralJsonBytesSerDes serdes = new GeneralJsonBytesSerDes();
        assertArrayEquals(golden().getBytes(StandardCharsets.UTF_8), serdes.serialize(sample()));
        assertEquals("FATE-测试", serdes.deserialize(golden().getBytes(StandardCharsets.UTF_8), Sample.class).name);
        assertNull(serdes.serialize(null)); assertNull(serdes.deserialize(null, Sample.class));
        try { serdes.deserialize("wrong-transport", Sample.class); fail("wrong transport must fail"); }
        catch (IllegalArgumentException expected) { assertTrue(expected.getMessage().contains("Type error")); }
    }
    @Test public void actualResultAndObjectTransformRemainUsable() throws Exception {
        ReturnResult result = new ReturnResult(); result.setRetcode(7); result.setRetmsg("测试");
        result.getData().put("payload", "ordinary");
        JsonNode tree = new ObjectMapper().readTree(result.toString());
        assertEquals(7, tree.get("retcode").intValue());
        assertEquals("ordinary", tree.get("data").get("payload").asText());
        Sample value = (Sample) ObjectTransform.json2Bean(ObjectTransform.bean2Json(sample()), Sample.class);
        assertEquals("FATE-测试", value.name); assertEquals(7, value.count);
        assertEquals("", ObjectTransform.bean2Json(null)); assertNull(ObjectTransform.json2Bean("", Sample.class));
    }
    @Test public void actualMalformedJsonKeepsFailureContract() {
        GeneralJsonStringSerDes serdes = new GeneralJsonStringSerDes();
        try { serdes.deserialize("[", Sample.class); fail("malformed JSON must fail"); }
        catch (RuntimeException expected) { assertTrue(expected.getMessage().startsWith("Failed to deserialize")); assertNotNull(expected.getCause()); }
    }
    public static class InertDenied {
        static int constructions;
        public String value;
        public InertDenied() { constructions++; }
    }
    public static class TypedValue {
        @JsonTypeInfo(use = JsonTypeInfo.Id.CLASS, include = JsonTypeInfo.As.WRAPPER_ARRAY)
        public Object value;
    }
    @Test public void deniedGenericTypeArgumentCannotInstantiateInertBean() throws Exception {
        BasicPolymorphicTypeValidator ptv = BasicPolymorphicTypeValidator.builder().allowIfSubType("java.util.ArrayList").build();
        ObjectMapper mapper = new ObjectMapper(); mapper.setPolymorphicTypeValidator(ptv);
        InertDenied.constructions = 0;
        String json = "{\"value\":[\"java.util.ArrayList<" + InertDenied.class.getName() + ">\",[{\"value\":\"inert\"}]]}";
        try { mapper.readValue(json, TypedValue.class); fail("generic allowlist bypass"); }
        catch (InvalidTypeIdException expected) { assertEquals(0, InertDenied.constructions); }
    }
    @Test public void deniedConcreteArrayComponentCannotInstantiateInertBean() throws Exception {
        BasicPolymorphicTypeValidator ptv = BasicPolymorphicTypeValidator.builder().allowIfSubTypeIsArray().allowIfSubType(String.class).build();
        ObjectMapper mapper = new ObjectMapper(); mapper.setPolymorphicTypeValidator(ptv);
        InertDenied.constructions = 0;
        String json = "{\"value\":[\"[L" + InertDenied.class.getName() + ";\",[{\"value\":\"inert\"}]]}";
        try { mapper.readValue(json, TypedValue.class); fail("array allowlist bypass"); }
        catch (InvalidTypeIdException expected) { assertEquals(0, InertDenied.constructions); }
        String allowed = "{\"value\":[\"[Ljava.lang.String;\",[\"ordinary\"]]}";
        assertArrayEquals(new String[]{"ordinary"}, (String[]) mapper.readValue(allowed, TypedValue.class).value);
    }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "kind", defaultImpl = Fallback.class)
    public static abstract class Named { public int value; }
    public static class Fallback extends Named { }
    private Named readNamed(ObjectMapper mapper, TypeDeserializer td, String id) throws Exception {
        try (JsonParser parser = mapper.getFactory().createParser("{\"kind\":\""+id+"\",\"value\":7}")) {
            parser.nextToken();
            DefaultDeserializationContext context = ((DefaultDeserializationContext) mapper.getDeserializationContext())
                .createInstance(mapper.getDeserializationConfig(), parser, null);
            return (Named) td.deserializeTypedFromObject(parser, context);
        }
    }
    @Test public void unknownFallbackTypeIdRetentionIsBounded() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        TypeDeserializer td = mapper.getDeserializationConfig().findTypeDeserializer(mapper.constructType(Named.class));
        Field field = TypeDeserializerBase.class.getDeclaredField("_deserializers"); field.setAccessible(true);
        for (int i=0; i<1100; i++) assertEquals(7, readNamed(mapper, td, "unknown-"+i).value);
        int distinct = ((Map<?,?>) field.get(td)).size();
        for (int i=0; i<32; i++) assertEquals(7, readNamed(mapper, td, "repeated").value);
        System.out.println("unknown fallback IDs=1100, retained="+distinct);
        assertTrue("unknown fallback retention must stay <=1000; actual="+distinct, distinct<=1000);
        assertTrue(((Map<?,?>) field.get(td)).size()<=1000);
    }
    public static final class CountedId {
        static long comparisons;
        final String value;
        @JsonCreator public CountedId(String value) { this.value=value; }
        @JsonValue public String value() { return value; }
        @Override public int hashCode() { return value.hashCode(); }
        @Override public boolean equals(Object other) { comparisons++; return other instanceof CountedId && value.equals(((CountedId)other).value); }
    }
    @JsonIdentityInfo(generator=ObjectIdGenerators.PropertyGenerator.class, property="id")
    public static class IdentityValue { public CountedId id; public int value; }
    @Test public void reverseForwardReferencesKeepOrderWithLinearComparisonBudget() throws Exception {
        final int n=64; StringBuilder json=new StringBuilder("[");
        for(int i=0;i<n;i++) { if(i>0)json.append(','); json.append('"').append("id").append(i).append('"'); }
        for(int i=n-1;i>=0;i--) json.append(",{\"id\":\"id").append(i).append("\",\"value\":").append(i).append('}');
        json.append(']'); assertTrue(json.length()<4096); CountedId.comparisons=0;
        List<IdentityValue> values=new ObjectMapper().readValue(json.toString(), new com.fasterxml.jackson.core.type.TypeReference<List<IdentityValue>>(){});
        assertEquals(2*n, values.size());
        for(int i=0;i<n;i++){ assertEquals(i,values.get(i).value); assertSame(values.get(i),values.get(2*n-1-i)); }
        long comparisons=CountedId.comparisons; System.out.println("reverse refs="+n+", ID comparisons="+comparisons);
        assertTrue("finite reverse-resolution comparison budget; actual="+comparisons,comparisons<=8*n);
    }
}
