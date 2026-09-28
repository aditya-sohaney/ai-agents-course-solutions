# ADR: Keep Specialist Handoffs Explicit

The system passes frozen dataclasses rather than sharing a mutable message history. Evidence scouting runs in parallel and improves coverage for a small latency cost. Claim review adds clear value by rejecting the injected document and preserving conflicting mentoring estimates. The writer adds cost only after evidence is accepted.

If simplifying, we would combine query expansion with the Evidence Scout before removing review. The single-agent baseline leaves one unsupported claim per answer in this fixture, while review eliminates that class of error. We would not add more agents without a measured failure that needs a distinct responsibility.

