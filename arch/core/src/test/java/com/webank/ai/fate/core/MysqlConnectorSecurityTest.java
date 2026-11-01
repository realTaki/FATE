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

import java.sql.Driver;
import java.sql.DriverPropertyInfo;
import java.util.Properties;
import org.junit.Test;
import static org.junit.Assert.*;

/** JDBC metadata only: no connection, credentials, database or FATE service. */
public class MysqlConnectorSecurityTest {
    private Driver driver() throws Exception {
        return (Driver) Class.forName("com.mysql.cj.jdbc.Driver")
                .getDeclaredConstructor().newInstance();
    }

    @Test
    public void configuredDriverRetainsJava8CompatibleFixedVersion() throws Exception {
        Driver driver = driver();
        assertEquals(8, driver.getMajorVersion());
        assertEquals(2, driver.getMinorVersion());
    }

    @Test
    public void ordinaryJdbcUrlAndEncodingAreRetained() throws Exception {
        Driver driver = driver();
        String url = "jdbc:mysql://127.0.0.1:9/synthetic"
                + "?useUnicode=true&characterEncoding=UTF-8&useSSL=true";
        assertTrue(driver.acceptsURL(url));
        assertFalse(driver.acceptsURL("jdbc:other:synthetic"));
        boolean encodingFound = false;
        for (DriverPropertyInfo property : driver.getPropertyInfo(url, new Properties())) {
            if ("characterEncoding".equals(property.name)) {
                assertEquals("UTF-8", property.value);
                encodingFound = true;
            }
        }
        assertTrue(encodingFound);
    }

    @Test
    public void unsafeBlobAutoDeserializePropertyIsRemoved() throws Exception {
        for (DriverPropertyInfo property : driver().getPropertyInfo(
                "jdbc:mysql://127.0.0.1:9/synthetic", new Properties())) {
            assertNotEquals("autoDeserialize", property.name);
        }
    }
}
