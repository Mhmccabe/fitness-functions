package example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.util.UUID;

/**
 * CorrelationFilter — sets MDC correlation context for every inbound HTTP request.
 *
 * This is the "observability boundary": every log line emitted during request
 * processing carries the correlation ID without callers needing to thread it
 * through their parameters.
 *
 * Fitness function context:
 *   The rule "all HTTP requests must have a correlation ID in MDC" cannot be
 *   enforced by SonarQube. It is enforced by the Semgrep rule
 *   require-mdc-correlation-id combined with an architecture test (e.g. ArchUnit)
 *   verifying that CorrelationFilter is registered in the filter chain.
 */
public class CorrelationFilter implements Filter {

    private static final Logger log = LoggerFactory.getLogger(CorrelationFilter.class);

    static final String CORRELATION_HEADER = "X-Correlation-ID";
    static final String MDC_KEY = "correlationId";

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        // Accept incoming correlation ID (from upstream service) or generate one
        String correlationId = httpRequest.getHeader(CORRELATION_HEADER);
        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        MDC.put(MDC_KEY, correlationId);
        // Echo the correlation ID back so the caller can trace their request
        httpResponse.setHeader(CORRELATION_HEADER, correlationId);

        log.debug("request.started method={} uri={}",
                httpRequest.getMethod(),
                httpRequest.getRequestURI());

        try {
            chain.doFilter(request, response);
        } finally {
            log.debug("request.completed status={}", httpResponse.getStatus());
            MDC.remove(MDC_KEY);
        }
    }
}
