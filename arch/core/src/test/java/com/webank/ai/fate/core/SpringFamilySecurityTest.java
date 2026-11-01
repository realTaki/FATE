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

import com.webank.ai.fate.core.async.DefaultListenableFutureCallBack;
import com.webank.ai.fate.core.factory.AsyncModelFactory;
import com.webank.ai.fate.core.factory.ReturnStatusFactory;
import com.webank.ai.fate.core.model.impl.SingleDelayedResult;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import org.junit.Test;
import org.springframework.beans.BeanWrapper;
import org.springframework.beans.MutablePropertyValues;
import org.springframework.beans.PropertyAccessorFactory;
import org.springframework.beans.factory.xml.PluggableSchemaResolver;
import org.springframework.beans.factory.xml.XmlBeanDefinitionReader;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.support.GenericApplicationContext;
import org.springframework.core.io.ClassPathResource;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.validation.DataBinder;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import static org.junit.Assert.*;

/** Real local Spring modules and actual project beans; no service/exploit chain. */
public class SpringFamilySecurityTest {
    @Test
    public void actualProjectPrototypesAndAutowiredContextRemainUsable() {
        CountDownLatch latch = new CountDownLatch(1);
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.getBeanFactory().registerSingleton("testLatch", latch);
            context.getBeanFactory().registerSingleton("testThrowable", new IllegalStateException("fixture"));
            context.register(AsyncModelFactory.class, DefaultListenableFutureCallBack.class,
                    ReturnStatusFactory.class, SingleDelayedResult.class);
            context.refresh();
            AsyncModelFactory factory = context.getBean(AsyncModelFactory.class);
            DefaultListenableFutureCallBack<String> first = factory.createDefaultListenableCallback(String.class);
            DefaultListenableFutureCallBack<String> second = factory.createDefaultListenableCallback(String.class);
            assertNotSame(first, second);
            first.onSuccess("synthetic");
            assertEquals(0, latch.getCount());
            second.onFailure(new IllegalArgumentException("synthetic"));
            assertEquals(2, ((List<?>) ReflectionTestUtils.getField(second, "throwables")).size());
            ReturnStatusFactory status = context.getBean(ReturnStatusFactory.class);
            assertNotSame(status, context.getBean(ReturnStatusFactory.class));
            assertEquals("ok", status.createSucessful("ok").getMessage());
            SingleDelayedResult<String> result = context.getBean(SingleDelayedResult.class);
            result.setResult("payload");
            assertEquals("payload", result.getResultNow());
        }
    }

    @Test
    public void originalProjectXmlDefinitionsParseWithoutStartingServices() throws Exception {
        try (GenericApplicationContext context = new GenericApplicationContext()) {
            XmlBeanDefinitionReader reader = new XmlBeanDefinitionReader(context);
            final PluggableSchemaResolver local = new PluggableSchemaResolver(getClass().getClassLoader());
            reader.setEntityResolver((publicId, systemId) -> {
                InputSource resolved = local.resolveEntity(publicId, systemId);
                if (resolved == null) throw new SAXException("External schema lookup forbidden");
                return resolved;
            });
            reader.loadBeanDefinitions(new ClassPathResource("applicationContext-core.xml"));
            assertTrue(context.containsBeanDefinition("asyncThreadPool"));
            assertTrue(context.containsBeanDefinition("grpcServiceExecutor"));
            assertTrue(context.containsBeanDefinition("routineScheduler"));
            assertFalse(context.isActive()); // Never refresh this production-scanning context.
        }
    }

    @Test
    public void ordinaryWritableBeanBindingIsPreserved() {
        Form form = new Form();
        DataBinder binder = new DataBinder(form);
        MutablePropertyValues values = new MutablePropertyValues();
        values.add("name", "ordinary");
        binder.bind(values);
        assertEquals("ordinary", form.getName());
        assertFalse(binder.getBindingResult().hasErrors());
    }

    @Test
    public void disallowedFieldMatchingIsAsciiCaseInsensitive() {
        Form form = new Form();
        DataBinder binder = new DataBinder(form);
        binder.setDisallowedFields("SeCrEt");
        binder.bind(new MutablePropertyValues().add("secret", "untrusted"));
        assertEquals("unchanged", form.getSecret());
        assertArrayEquals(new String[] {"secret"}, binder.getBindingResult().getSuppressedFields());
    }

    @Test
    public void readOnlyAutoCloseablePropertiesAreNotIntrospected() {
        BeanWrapper wrapper = PropertyAccessorFactory.forBeanPropertyAccess(new Form());
        assertFalse(wrapper.isReadableProperty("inputStream"));
        assertTrue(wrapper.isReadableProperty("name"));
    }

    @Test
    public void classConcreteMetadataIsNotExposedAsBeanProperties() {
        BeanWrapper wrapper = PropertyAccessorFactory.forBeanPropertyAccess(new Form());
        assertTrue(wrapper.isReadableProperty("class.name"));
        assertFalse(wrapper.isReadableProperty("class.declaredMethods"));
        // Interface-inherited AnnotatedElement properties are not claimed blocked.
        // Java8 has no Class.module; this is a policy regression, not Spring4Shell RCE.
    }

    public static class Form {
        private String name = "initial";
        private String secret = "unchanged";
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getSecret() { return secret; }
        public void setSecret(String secret) { this.secret = secret; }
        public InputStream getInputStream() { return new ByteArrayInputStream(new byte[0]); }
    }
}
