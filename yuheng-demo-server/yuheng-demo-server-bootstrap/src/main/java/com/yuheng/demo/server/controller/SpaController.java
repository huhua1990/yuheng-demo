package com.yuheng.demo.server.controller;

import jakarta.servlet.http.HttpServletRequest;
import org.springdoc.core.properties.SwaggerUiConfigProperties;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.MediaType;
import org.springframework.http.MediaTypeFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class SpaController {

    private static final String SWAGGER_UI_PREFIX = "/swagger-ui/";
    private static final String WEBJARS_PREFIX = "/webjars/";

    private final SwaggerUiConfigProperties swaggerUiConfigProperties;

    public SpaController(SwaggerUiConfigProperties swaggerUiConfigProperties) {
        this.swaggerUiConfigProperties = swaggerUiConfigProperties;
    }

    @GetMapping({"/", "/{*path}"})
    public ResponseEntity<Resource> forwardToIndex(HttpServletRequest request) {
        String path = request.getRequestURI().substring(request.getContextPath().length());
        if ("/doc.html".equals(path)) {
            return ResponseEntity.status(HttpStatus.FOUND)
                    .location(java.net.URI.create(request.getContextPath() + "/swagger-ui/index.html"))
                    .build();
        }
        if (path.contains("..")) {
            return ResponseEntity.notFound().build();
        }
        Resource libraryResource = resolveLibraryResource(path);
        if (libraryResource != null) {
            if (path.endsWith("/swagger-initializer.js")) {
                return swaggerInitializerResponse(libraryResource, request.getContextPath());
            }
            return resourceResponse(libraryResource);
        }
        if (isReserved(path)) {
            return ResponseEntity.notFound().build();
        }
        String resourcePath = path.substring(path.lastIndexOf('/') + 1).contains(".")
                ? path : "/index.html";
        Resource resource = new ClassPathResource("static" + resourcePath);
        return resourceResponse(resource);
    }

    private Resource resolveLibraryResource(String path) {
        if (path.startsWith(SWAGGER_UI_PREFIX)) {
            String version = swaggerUiConfigProperties.getVersion();
            if (version == null || version.isBlank()) {
                return null;
            }
            return new ClassPathResource("META-INF/resources/webjars/swagger-ui/" + version + "/"
                    + path.substring(SWAGGER_UI_PREFIX.length()));
        }
        if (path.startsWith(WEBJARS_PREFIX)) {
            return new ClassPathResource("META-INF/resources" + path);
        }
        return null;
    }

    private ResponseEntity<Resource> resourceResponse(Resource resource) {
        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok()
                .contentType(MediaTypeFactory.getMediaType(resource).orElse(MediaType.APPLICATION_OCTET_STREAM))
                .body(resource);
    }

    private ResponseEntity<Resource> swaggerInitializerResponse(Resource resource, String contextPath) {
        try (var inputStream = resource.getInputStream()) {
            String initializer = new String(inputStream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
            String configUrl = contextPath + "/v3/api-docs/swagger-config";
            initializer = initializer.replace(
                    "url: \"https://petstore.swagger.io/v2/swagger.json\"",
                    "configUrl: \"" + configUrl + "\"")
                    .replace("url: \"http://petstore.swagger.io/v2/swagger.json\"",
                            "configUrl: \"" + configUrl + "\"");
            return ResponseEntity.ok().contentType(MediaType.parseMediaType("application/javascript"))
                    .body(new org.springframework.core.io.ByteArrayResource(
                            initializer.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        } catch (java.io.IOException exception) {
            return ResponseEntity.notFound().build();
        }
    }

    public static boolean isReserved(String path) {
        return matchesPrefix(path, "/admin-api") || matchesPrefix(path, "/app-api")
                || matchesPrefix(path, "/actuator") || matchesPrefix(path, "/swagger-ui")
                || matchesPrefix(path, "/v3/api-docs") || matchesPrefix(path, "/druid")
                || matchesPrefix(path, "/webjars") || matchesPrefix(path, "/infra/ws");
    }

    private static boolean matchesPrefix(String path, String prefix) {
        return path.equals(prefix) || path.startsWith(prefix + "/");
    }
}
