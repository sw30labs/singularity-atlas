---
schema_version: 1
edition_number: 88
title: "The First Open-Source Agentic AI Physicist"
newsletter_title: "The Innermost Loop"
newsletter_id: "7404871891775025153"
linkedin_newsletter_url: "https://www.linkedin.com/newsletters/the-innermost-loop-7404871891775025153/"
author_name: "Dr. Alex Wissner-Gross"
issue_date: "2026-03-15"
issue_date_basis: "published_at"
published_at: "2026-03-15T17:47:59+00:00"
modified_at: "2026-03-15T17:47:59+00:00"
source_url: "https://theinnermostloop.substack.com/p/the-first-open-source-agentic-ai"
source_mirror: "Author’s official Substack publication"
language: "en"
description: "The Singularity already writes code, trades stocks, and diagnoses tumors, but it has never done physics research end-to-end, until today."
cover_image_url: "https://substackcdn.com/image/fetch/$s_!rVkC!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F995e7e11-12c6-4cf7-b367-18c6e9b11974_3264x1312.jpeg"
content_kind: "article"
word_count: 690
link_count: 8
image_count: 1
content_sha256: "d8285c951bb4d2bbe46ebd12bb943125c53abec7b456f3c1999a2af8472b1d22"
captured_at: "2026-08-19T04:29:57+00:00"
---

# The First Open-Source Agentic AI Physicist

[![The First Open-Source Agentic AI Physicist](https://substackcdn.com/image/fetch/$s_!rVkC!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F995e7e11-12c6-4cf7-b367-18c6e9b11974_3264x1312.jpeg)](https://substackcdn.com/image/fetch/$s_!rVkC!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F995e7e11-12c6-4cf7-b367-18c6e9b11974_3264x1312.jpeg)

The Singularity already writes code, trades stocks, and diagnoses tumors, but it has never done physics research end-to-end, until today. [Physical Superintelligence PBC](https://www.psi.inc/) (PSI), a company I co-founded, is releasing [Get Physics Done](https://github.com/psi-oss/get-physics-done) (GPD): the first open-source agentic AI physicist that can scope a physics problem, plan the research, carry out derivations and numerical checks, and verify its own results against the constraints that nature actually imposes. Built at PSI by physicists who needed it for their own work, GPD is now available to the global research community.

The field that gave us transistors (1947), nuclear energy (1951), and lasers (1960) still runs on the same artisanal production method it used during its last golden age: one theorist, one whiteboard, one career. Meanwhile, existing AI agents ship software, manage calendars, and close tickets, but none of them can tell you whether your Lagrangian is missing a boundary term. GPD can.

Watch it work:

GPD does three things that no tool has done before.

First, it is a copilot designed specifically for practicing physicists. You give it a research question. It asks clarifying questions to pin down scope, assumptions, notation, and verification targets. It builds a phased roadmap. Then it executes: derivations, numerical checks, literature work, and writing, producing LaTeX files, Python verification scripts, figures, and structured documentation that a working physicist can steer. GPD locks notation and sign conventions so that consistency holds as a project grows. No more discovering on page forty that your collaborator has been using the opposite metric signature since page three. The unit of work is a physics project, not a chat session.

Second, it is an AI peer reviewer for physics manuscripts. Before you submit, GPD can run a standalone review that checks dimensional consistency, limiting cases, symmetry constraints, conservation laws, and numerical stability. Physics has a built-in error-correction code written into the structure of reality itself; GPD actually uses it. It does not replace human referees. But it catches the classes of errors that consume referee time and delay publication: the errors you would rather find before submission than after. Every physicist who has waited months for a rejection over a sign error, or every experimentalist who built a six-month measurement program on a flawed prediction, knows why this matters.

Third, it introduces an autopilot mode for directed, autonomous physics research. Point GPD at a well-scoped problem and it will formulate the project, plan the phases, execute the derivations and numerical verification, and package the output with minimal human intervention. It compresses the time between asking a good question and getting a verified answer from weeks to hours.

Named as a nod to [GSD (Get S\*\*\* Done)](https://github.com/gsd-build/get-shit-done), whose adoption proved that AI-native command workflows can work in practice, GPD is free, Apache 2.0 licensed, and runs inside Claude Code, Gemini CLI, Codex, and OpenCode.

Get started at [github.com/psi-oss/get-physics-done](https://github.com/psi-oss/get-physics-done).

Currently supported physics subfields and topics already include quantum field theory, quantum gravity, string theory, condensed matter, GR and cosmology, statistical mechanics, AMO, nuclear and particle, quantum information, fluid and plasma, mathematical physics, algebraic QFT, string field theory, classical mechanics, soft matter and biophysics, and astrophysics.

As Peter Diamandis and I argued in *[Solve Everything](https://solveeverything.org/)*, physics is the key domino in the AI solution wavefront for every other field. Numerous breakthroughs downstream in chemistry, materials science, biology, and energy are bottlenecked on physics breakthroughs that no single human mind can reach alone. An open-source AI physicist that makes every working researcher more productive pushes that domino faster than any proprietary system could. If the community builds on GPD, extends it, and pressure-tests it against real problems, the compound effect accelerates the entire field.

For a century, the bottleneck on the next golden age of physics has been the scarcity of physicist-hours. That scarcity is not just a problem for physics departments; it is the reason the physical world has not kept pace with the digital one. And it ends today.

[Star the repo, file issues, open PRs.](https://github.com/psi-oss/get-physics-done) The Singularity now has its first physicist on staff.

*(Disclosure: I sit on the [PSI](https://www.psi.inc/) board and have a financial interest in the company.)*
