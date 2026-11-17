package com.yuheng.demo.server.config;

import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.server.support.WebSocketHandlerMapping;

@Configuration(proxyBeanMethods = false)
public class WebSocketHandlerMappingOrderConfiguration {

    @Bean
    static BeanPostProcessor orderWebSocketHandlerMapping() {
        return new BeanPostProcessor() {
            @Override
            public Object postProcessAfterInitialization(Object bean, String beanName) {
                if ("webSocketHandlerMapping".equals(beanName) && bean instanceof WebSocketHandlerMapping mapping) {
                    mapping.setOrder(-1);
                }
                return bean;
            }
        };
    }
}
