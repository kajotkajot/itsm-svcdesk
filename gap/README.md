<!-- ai-generated: 100% - documented the client/server latency difference from the measured Toxiproxy experiment -->
# Client-server latency gap

For the local measurement, a Toxiproxy 2.12.0 proxy sat between the load generator and `svcdesk`. Its downstream latency toxic was configured with 100 ms latency, 10 ms jitter, and full toxicity. The proxy forwarded to `svcdesk:8080`; the request still made its single upstream call to `kb-index`.

The open-loop client p99 was 246.6 ms, while the svcdesk request histogram reported a p99 of 140.0 ms over the same measurement. The recorded client-server gap is therefore 106.6 ms. Most of that additional time is consistent with the configured downstream toxic; the remainder can include jitter, scheduling, network transit, and the difference between independently estimated percentiles. The figures are a single finite sample, not a claim that every request gained exactly 100 ms.

This distinction matters operationally: the client experiences waiting outside the server's measured request interval, so the server histogram alone cannot explain the full end-to-end latency. The Lab 3 checker repeats a shorter measurement with the toxic values declared in `gap.json` and evaluates the difference using its own client and server p99 measurements.
