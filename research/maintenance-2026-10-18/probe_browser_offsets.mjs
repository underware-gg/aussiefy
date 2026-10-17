// Apply a real alternative from the Python API using the documented Unicode code-point offsets.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const { browser_case: result } = JSON.parse(readFileSync(0, "utf8"));
const change = result.changes.find(c => c.alternatives.some(o => o.rendered !== c.output));
assert.ok(change, "The case needs an actual alternative");
const option = change.alternatives.find(o => o.rendered !== change.output);
const points = Array.from(result.text);
const [start, end] = option.out_span;
const current = points.slice(start, end).join("");
assert.equal(current, change.output);
assert.notEqual(result.text.slice(start, end), current, "Emoji must expose UTF-16 indexing drift");
const swapped = [...points.slice(0, start), option.rendered, ...points.slice(end)].join("");
assert.ok(swapped.startsWith("🦘 My car is "));
assert.ok(swapped.endsWith("."));
assert.equal(Array.from(swapped).slice(start, start + Array.from(option.rendered).length).join(""), option.rendered);
console.log(JSON.stringify({ node: process.versions.node, original: result.text, span: option.out_span,
  selected: current, replacement: option.rendered, swapped, utf16_slice_differs: true }, null, 2));
