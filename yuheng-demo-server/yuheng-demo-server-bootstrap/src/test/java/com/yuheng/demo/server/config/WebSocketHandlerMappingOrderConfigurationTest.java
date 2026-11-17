package com.yuheng.demo.server.config;

import org.junit.jupiter.api.Test;
import org.springframework.web.socket.server.support.WebSocketHandlerMapping;

import static org.junit.jupiter.api.Assertions.assertTrue;

class WebSocketHandlerMappingOrderConfigurationTest {

    @Test
    void webSocketMappingRunsBeforeSpaCatchAllMapping() {
        WebSocketHandlerMapping mapping = new WebSocketHandlerMapping();

        WebSocketHandlerMappingOrderConfiguration.orderWebSocketHandlerMapping().postProcessAfterInitialization(
                mapping, "webSocketHandlerMapping");

        assertTrue(mapping.getOrder() < 0,
                "WebSocket handshake mapping must run before Spring MVC request mappings and the SPA catch-all");
    }
}
