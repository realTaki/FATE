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

import com.webank.ai.fate.core.bean.FederatedRoles;
import com.webank.ai.fate.core.error.exception.MultipleRuntimeThrowables;
import com.webank.ai.fate.core.retry.Retryer;
import com.webank.ai.fate.core.retry.factory.RetryerBuilder;
import com.webank.ai.fate.core.retry.factory.StopStrategies;
import com.webank.ai.fate.core.utils.FederatedUtils;
import com.webank.ai.fate.core.utils.SceneUtils;
import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.commons.lang3.StringUtils;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.Description;
import org.junit.runners.model.Statement;
import static org.junit.Assert.*;

/** Ordinary offline API and real utility regressions; no resource-exhaustion inputs. */
public class LangJunitCompatibilityTest {
    @Test
    public void actualFederatedIdentificationSortsAndDeduplicatesParties() {
        FederatedRoles roles = new FederatedRoles();
        roles.setRole("host", Arrays.asList("200", "100", "200"));
        roles.setRole("guest", Arrays.asList("999"));
        assertEquals("guest-999#host-100_200",
                FederatedUtils.federatedRolesIdentificationString(roles));
        assertEquals(Arrays.asList("200", "100", "200"), roles.getRole("host"));
    }

    @Test
    public void actualFederatedIdentificationRetainsNullAndEmptyConventions() {
        assertEquals("all", FederatedUtils.federatedRolesIdentificationString(null));
        assertEquals("", FederatedUtils.federatedRolesIdentificationString(new FederatedRoles()));
    }

    @Test
    public void actualSceneKeyRetainsSeparatorsAndUnicode() {
        FederatedRoles roles = new FederatedRoles();
        roles.setRole("host", Arrays.asList("100"));
        assertEquals("guest#\u914d\u7f6e#host-100", SceneUtils.genSceneKey("guest", "\u914d\u7f6e", roles));
        assertEquals("guest#100#all", SceneUtils.genSceneKey("guest", "100", null));
    }

    @Test
    public void actualMultipleThrowablesRetainsOrdinaryExceptionDiagnostics() {
        MultipleRuntimeThrowables combined = new MultipleRuntimeThrowables("synthetic",
                Arrays.<Throwable>asList(new IOException("first"), new IllegalArgumentException("second")));
        assertEquals("synthetic", combined.getMessage());
        assertNotNull(combined.getCause());
        String diagnostic = combined.getCause().getMessage();
        assertTrue(diagnostic.contains("idx: 0\njava.io.IOException: first"));
        assertTrue(diagnostic.contains("idx: 1\njava.lang.IllegalArgumentException: second"));
    }

    @Test
    public void usedStringPredicatesRetainNullBlankAndOrdinarySemantics() {
        assertTrue(StringUtils.isEmpty(null));
        assertTrue(StringUtils.isEmpty(""));
        assertFalse(StringUtils.isEmpty(" "));
        assertTrue(StringUtils.isBlank(" \t\n"));
        assertFalse(StringUtils.isBlank("host"));
        assertTrue(StringUtils.isNotBlank("host"));
        assertTrue(StringUtils.isAllBlank(null, " "));
        assertTrue(StringUtils.isAnyBlank("host", ""));
        assertTrue(StringUtils.isNoneBlank("host", "100", "guest"));
        assertFalse(StringUtils.isNoneBlank("host", null));
    }

    @Test
    public void actualRetryBuilderRetainsBlankAndDuplicateDescriptionChecks() {
        RetryerBuilder<String> builder = RetryerBuilder.<String>newBuilder()
                .withDescription(" \t").withDescription("synthetic");
        try {
            builder.withDescription("replacement");
            fail("An existing nonblank description must be rejected");
        } catch (IllegalStateException expected) {
            assertTrue(expected.getMessage().contains("synthetic"));
        }
    }

    @Test
    public void actualRetryerRetainsOrdinarySuccessAndOneExceptionRetry() throws Exception {
        final AtomicInteger calls = new AtomicInteger();
        Retryer<String> retryer = RetryerBuilder.<String>newBuilder()
                .retryIfExceptionOfType(IOException.class)
                .withStopStrategy(StopStrategies.stopAfterMaxAttempt(2)).build();
        retryer.setDescription("synthetic");
        assertEquals("done", retryer.call(() -> {
            if (calls.incrementAndGet() == 1) throw new IOException("first attempt");
            return "done";
        }));
        assertEquals(2, calls.get());
        retryer.setDescription(" \t");
        assertEquals("direct", retryer.call(() -> "direct"));
    }

    @Test
    public void temporaryFolderCleansUpOrdinaryFilesAfterSuccess() throws Throwable {
        verifyTemporaryFolderCleanup(false);
    }

    @Test
    public void temporaryFolderCleansUpOrdinaryFilesAfterFailure() throws Throwable {
        verifyTemporaryFolderCleanup(true);
    }

    private void verifyTemporaryFolderCleanup(final boolean failBody) throws Throwable {
        final TemporaryFolder folder = new TemporaryFolder();
        final File[] createdRoot = new File[1];
        Statement body = new Statement() {
            @Override
            public void evaluate() throws Throwable {
                createdRoot[0] = folder.getRoot();
                assertTrue(folder.newFile("synthetic.txt").isFile());
                assertTrue(folder.newFolder("nested", "child").isDirectory());
                if (failBody) throw new IOException("synthetic body failure");
            }
        };
        try {
            folder.apply(body, Description.createTestDescription(getClass(), "temporaryFixture")).evaluate();
            assertFalse("Expected the synthetic body failure", failBody);
        } catch (IOException expected) {
            assertTrue(failBody);
            assertEquals("synthetic body failure", expected.getMessage());
        }
        assertNotNull(createdRoot[0]);
        assertFalse("The rule must remove its fixture directory", createdRoot[0].exists());
    }
}
