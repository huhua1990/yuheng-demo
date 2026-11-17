package com.yuheng.demo.server.controller;

import jakarta.servlet.http.HttpServletRequest;
import org.junit.jupiter.api.Test;
import org.springdoc.core.properties.SwaggerUiConfigProperties;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpStatus;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SpaControllerTest {

    private final SwaggerUiConfigProperties swaggerUiConfigProperties = swaggerUiConfigProperties();
    private final SpaController controller = new SpaController(swaggerUiConfigProperties);

    @Test
    void servesSwaggerUiClasspathResources() {
        ResponseEntity<Resource> response = controller.forwardToIndex(request("/swagger-ui/index.html"));

        assertEquals(200, response.getStatusCode().value());
        assertTrue(response.getHeaders().getContentType().isCompatibleWith(org.springframework.http.MediaType.TEXT_HTML));
        assertNotNull(response.getBody());
        assertTrue(response.getBody().exists());
    }

    @Test
    void configuresSwaggerUiToLoadYuhengApiGroups() throws Exception {
        ResponseEntity<Resource> response = controller.forwardToIndex(request("/swagger-ui/swagger-initializer.js"));

        assertEquals(200, response.getStatusCode().value());
        String initializer = new String(response.getBody().getContentAsByteArray(),
                java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(initializer.contains("configUrl: \"/v3/api-docs/swagger-config\""));
        assertTrue(!initializer.contains("url: \"/v3/api-docs/swagger-config\""));
    }

    @Test
    void servesWebjarResourcesWithTheirMediaType() {
        ResponseEntity<Resource> response = controller.forwardToIndex(
                request("/webjars/swagger-ui/5.32.2/swagger-ui.css"));

        assertEquals(200, response.getStatusCode().value());
        assertTrue(response.getHeaders().getContentType().isCompatibleWith(
                org.springframework.http.MediaType.parseMediaType("text/css")));
        assertNotNull(response.getBody());
        assertTrue(response.getBody().exists());
    }

    @Test
    void keepsApiPathsOutOfSpaFallback() {
        ResponseEntity<Resource> response = controller.forwardToIndex(request("/admin-api/system/user/page"));

        assertEquals(404, response.getStatusCode().value());
    }

    @Test
    void redirectsLegacyKnife4jUrlToSwaggerUi() {
        ResponseEntity<Resource> response = controller.forwardToIndex(request("/doc.html"));

        assertEquals(HttpStatus.FOUND, response.getStatusCode());
        assertEquals("/swagger-ui/index.html", response.getHeaders().getLocation().getPath());
    }

    private static HttpServletRequest request(String uri) {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", uri);
        request.setRequestURI(uri);
        request.setServletPath(uri);
        return request;
    }

    private static SwaggerUiConfigProperties swaggerUiConfigProperties() {
        SwaggerUiConfigProperties properties = new SwaggerUiConfigProperties();
        properties.setVersion("5.32.2");
        return properties;
    }
}
