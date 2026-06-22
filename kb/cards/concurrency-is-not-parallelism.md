---
id: concurrency-is-not-parallelism
title: "Concurrency Is Not Parallelism"
creator: "Rob Pike"
year: 2012
format: Talk
category: Engineering and Systems
subcategory: Concurrency
difficulty: Intermediate
credibility: 9
usefulness: 8
status: recommended
---

# Concurrency Is Not Parallelism

**Rob Pike** · 2012 · Talk
**Category:** Engineering and Systems → Concurrency
**Difficulty:** Intermediate · **Status:** `recommended` · **Credibility:** 9/10 · **Usefulness:** 8/10

## Summary
A crisp talk by a co-creator of Go drawing the distinction between concurrency (structuring a program as independently executing parts) and parallelism (executing them simultaneously). Clears up a near-universal confusion.

## Key takeaways
- Concurrency is about structure; parallelism is about execution.
- Good concurrent design composes independent pieces that may or may not run in parallel.
- Better mental models lead to simpler, more robust systems.

## Why it matters
A short talk that permanently sharpens how you reason about concurrent software.

## Audience fit
Software engineers, especially systems and backend.

## Tags
`concurrency` `parallelism` `go` `talk` `systems`

## Source
[https://go.dev/blog/waza-talk](https://go.dev/blog/waza-talk)

---
*Part of the [Tech Research Knowledge Base](../../indexes/master.md). Generated from `indexes/master.json` — edit there, not here.*
