package com.yuheng.demo.server.config;

import com.yuheng.demo.server.controller.SpaController;
import com.yuheng.platform.framework.security.config.AuthorizeRequestsCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AuthorizeHttpRequestsConfigurer;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerExecutionChain;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

@Configuration(proxyBeanMethods = false)
public class SpaSecurityConfiguration {

    @Bean
    public AuthorizeRequestsCustomizer spaAuthorizeRequestsCustomizer(RequestMappingHandlerMapping requestMappingHandlerMapping) {
        return new AuthorizeRequestsCustomizer() {
            @Override
            public void customize(AuthorizeHttpRequestsConfigurer<HttpSecurity>.AuthorizationManagerRequestMatcherRegistry registry) {
                registry.requestMatchers(request -> {
                    if (!HttpMethod.GET.matches(request.getMethod()) || SpaController.isReserved(request.getServletPath())) {
                        return false;
                    }
                    try {
                        HandlerExecutionChain chain = requestMappingHandlerMapping.getHandler(request);
                        return chain != null && chain.getHandler() instanceof HandlerMethod handler
                                && handler.getBeanType().equals(SpaController.class);
                    } catch (Exception ex) {
                        return false;
                    }
                }).permitAll();
            }
        };
    }
}
