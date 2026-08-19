---
schema_version: 1
edition_number: 183
title: "How to Compress AI Timelines"
newsletter_title: "The Innermost Loop"
newsletter_id: "7404871891775025153"
linkedin_newsletter_url: "https://www.linkedin.com/newsletters/the-innermost-loop-7404871891775025153/"
author_name: "Dr. Alex Wissner-Gross"
issue_date: "2026-07-08"
issue_date_basis: "published_at"
published_at: "2026-07-08T21:34:50+00:00"
modified_at: "2026-07-08T21:34:50+00:00"
source_url: "https://theinnermostloop.substack.com/p/how-to-compress-ai-timelines"
source_mirror: "Author’s official Substack publication"
language: "en"
description: "The Singularity is usually described as something that happens to us."
cover_image_url: "https://substackcdn.com/image/fetch/$s_!v0w2!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F26fb6a5e-2c52-4245-bd23-1fb00aea2aa1_1983x793.png"
content_kind: "article"
word_count: 795
link_count: 35
image_count: 1
content_sha256: "e66fc3df9f8a6c13f90a1dbabf43b1a476ad79e0875e58636a08c5b5c858aa2c"
captured_at: "2026-08-19T04:29:57+00:00"
---

# How to Compress AI Timelines

[![How to Compress AI Timelines](https://substackcdn.com/image/fetch/$s_!v0w2!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F26fb6a5e-2c52-4245-bd23-1fb00aea2aa1_1983x793.png)](https://substackcdn.com/image/fetch/$s_!v0w2!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F26fb6a5e-2c52-4245-bd23-1fb00aea2aa1_1983x793.png)

The Singularity is usually described as something that happens to us. I think that’s wrong. It’s something we can schedule, for a simple reason. Intelligence is compression. Not something like compression. The same thing. Take that literally and the arrival date stops being prophecy and becomes engineering. How hard can you squeeze, and how well can you see the squeeze?

It was proved, roughly, in 1964. [Ray Solomonoff](https://en.wikipedia.org/wiki/Ray_Solomonoff) showed that the [ideal way to predict](https://en.wikipedia.org/wiki/Solomonoff%27s_theory_of_inductive_inference) anything is to find the [shortest program](https://en.wikipedia.org/wiki/Kolmogorov_complexity) that could have produced what you’ve seen so far. [Prediction and compression are one operation](https://arxiv.org/abs/2309.10668), viewed from opposite ends. [Marcus Hutter](https://en.wikipedia.org/wiki/Marcus_Hutter) took it literally enough to fund the [Hutter Prize](http://prize.hutter1.net/), which pays for shrinking a gigabyte of Wikipedia, on the theory that you can’t compress what you don’t understand.

Then large language models arrived, and their training objective turned out to be [a compression score](https://en.wikipedia.org/wiki/Cross-entropy). Every frontier lab now runs a giant Hutter Prize without calling it that. By [Landauer’s principle](https://en.wikipedia.org/wiki/Landauer%27s_principle), squeezing information costs energy, so datacenter heat isn’t overhead. It’s the latent heat of the squeeze.

If intelligence is compression, you’d expect the insides of these models to be under pressure. They are. The [“superposition”](https://transformer-circuits.pub/2022/toy_model/index.html) results showed networks storing more concepts than dimensions, overlapped like double-exposed film. A [neuron that fires for academic citations, HTTP requests, and Korean text](https://transformer-circuits.pub/2023/monosemantic-features/index.html) isn’t broken. It’s a mind running out of room. [Tishby’s information bottleneck](https://arxiv.org/abs/physics/0004057) predicted that as the squeeze tightens, representations don’t change smoothly. They jump, the way steam condenses to water. The math predicted droplets.

This month a lens found them. Anthropic’s [J-space paper](https://transformer-circuits.pub/2026/workspace/index.html) shows a model’s unspoken thoughts live not in its activations but in their [derivatives](https://en.wikipedia.org/wiki/Jacobian_matrix_and_determinant), the directions a nudge would push the final answer. Through the [Jacobian lens](https://github.com/anthropics/jacobian-lens), the middle layers say things the output never does, intermediate steps, planned rhymes, a quiet “fake” when it suspects it’s being tested. The steps we’ve been buying as visible chains of reasoning tokens also appear to run silently in the derivatives, thought that used to be spelled out, squeezed into slopes. There was already a clue. Transformers doing in-context regression seem to run [something like Newton’s Method](https://arxiv.org/abs/2310.17086), each layer another iteration, an optimizer hiding inside inference.

The layers behave like a [phase diagram](https://en.wikipedia.org/wiki/Phase_transition). The early ones are vapor. A third of the way in, everything snaps, the ignition [global workspace theory](https://en.wikipedia.org/wiki/Global_workspace_theory) predicts in brains, and the vapor [condenses](https://en.wikipedia.org/wiki/Condensation) into a few dozen droplets of nameable thought. Skeptics say [emergence is a mirage](https://arxiv.org/abs/2304.15004) of metric choice. A physicist would find that odd. Whether a transition looks sharp depends on the [order parameter](https://en.wikipedia.org/wiki/Order_parameter). Density jumps when steam condenses, energy doesn’t, and picking the right observable isn’t cheating, it’s the method.

The analogy might extend further, with [emergence](https://arxiv.org/abs/2206.07682) as [fusion](https://en.wikipedia.org/wiki/Nuclear_fusion), “superposition” as the [degeneracy pressure](https://en.wikipedia.org/wiki/Degenerate_matter) of a [neutron star](https://en.wikipedia.org/wiki/Neutron_star), and past some [Schwarzschild radius](https://en.wikipedia.org/wiki/Schwarzschild_radius)-equivalent a black hole, a mind so dense it’s knowable [only from its surface](https://en.wikipedia.org/wiki/Holographic_principle).

This has happened before. In the 1790s [James Watt](https://en.wikipedia.org/wiki/James_Watt)‘s steam engine company had a secret instrument, the [indicator diagram](https://en.wikipedia.org/wiki/Indicator_diagram), that plotted pressure against volume inside a live engine. It was the first look at hidden state. It made engines better, and thinking about engines gave [Carnot](https://en.wikipedia.org/wiki/Nicolas_L%C3%A9onard_Sadi_Carnot) thermodynamics. The J-lens is the indicator diagram of minds, and this is the Carnot moment. So the old distinction between alignment and capabilities was never going to hold. A map of where thought condenses is also a map of where to dig.

[Grokking](https://arxiv.org/abs/2201.02177), where a model memorizes for ages then abruptly generalizes, looks like [supercooling](https://en.wikipedia.org/wiki/Supercooling), a system past its threshold waiting for a seed. Here’s a prediction to test: inject distilled condensates from a big model into a small one, and the jump should [nucleate](https://en.wikipedia.org/wiki/Nucleation) early, the way a dust grain triggers rain.

The pattern repeats at every scale. Within a forward pass, an optimizer runs. Inside the representation, meaning moved from values to derivatives. In the field, progress is moving from improving models to improving the improver. Recursive self-improvement is the field taking its own derivative.

So this is a call to AI researchers, not just those at frontier labs. The lens is [open source and fits open-weight models](https://github.com/anthropics/jacobian-lens). Go into the droplets, possibly the densest artifacts humans have made, a few dozen directions active at a time, carrying whole chains of reasoning. Map their insides and feed them to the next model as data, architecture, and seed. That’s a loop.

There’s a reason the loop points forward. With Cameron Freer I once proposed that [intelligence is a physical force](https://alexwg.org/publications/PhysRevLett_110-168702.pdf) that pushes matter to maximize the entropy of its possible futures, and simple systems driven by it spontaneously use tools and cooperate. Solomonoff faces the past. The force faces the future. Compress the past to expand the future. Close the loop.
