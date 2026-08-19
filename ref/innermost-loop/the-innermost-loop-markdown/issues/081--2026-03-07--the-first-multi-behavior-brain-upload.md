---
schema_version: 1
edition_number: 81
title: "The First Multi-Behavior Brain Upload"
newsletter_title: "The Innermost Loop"
newsletter_id: "7404871891775025153"
linkedin_newsletter_url: "https://www.linkedin.com/newsletters/the-innermost-loop-7404871891775025153/"
author_name: "Dr. Alex Wissner-Gross"
issue_date: "2026-03-07"
issue_date_basis: "published_at"
published_at: "2026-03-07T09:44:58+00:00"
modified_at: "2026-03-07T09:44:58+00:00"
source_url: "https://theinnermostloop.substack.com/p/the-first-multi-behavior-brain-upload"
source_mirror: "Author’s official Substack publication"
language: "en"
description: "The Singularity has belonged exclusively to artificial minds, until now."
cover_image_url: "https://substackcdn.com/image/fetch/$s_!6AGg!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F90dee4e2-926c-4f00-beca-86545220210e_4314x1602.jpeg"
content_kind: "article"
word_count: 546
link_count: 14
image_count: 1
content_sha256: "a71e606a417f3311d1e89dc873d60dc92c15c3793b4437823fa5375d47ff3c34"
captured_at: "2026-08-19T04:29:57+00:00"
---

# The First Multi-Behavior Brain Upload

[![The First Multi-Behavior Brain Upload](https://substackcdn.com/image/fetch/$s_!6AGg!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F90dee4e2-926c-4f00-beca-86545220210e_4314x1602.jpeg)](https://substackcdn.com/image/fetch/$s_!6AGg!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F90dee4e2-926c-4f00-beca-86545220210e_4314x1602.jpeg)

The Singularity has belonged exclusively to artificial minds, until now. For decades, whole-brain emulation has been the tantalizing counterpart to artificial intelligence: copy a biological brain, neuron by neuron and synapse by synapse, and run it. Today, for the first time, I am releasing a video from a company I helped found, [Eon Systems PBC](https://eon.systems/), demonstrating what we believe is the world’s first embodiment of a whole-brain emulation that produces multiple behaviors.

Watch the video here:

In 2024, Eon senior scientist Philip Shiu and collaborators [published in](https://www.nature.com/articles/s41586-024-07763-9)*[Nature](https://www.nature.com/articles/s41586-024-07763-9)* a computational model of the entire adult *[Drosophila melanogaster](https://en.wikipedia.org/wiki/Drosophila_melanogaster)* brain, containing more than 125,000 neurons and 50 million synaptic connections, built from the [FlyWire](https://flywire.ai/) connectome and machine learning predictions of neurotransmitter identity. That model predicted motor behavior at 95% accuracy. But it was disembodied: a brain without a body, activation without physics, motor outputs with nowhere to go.

Now the brain has somewhere to go. Building on previous work, including Shiu et al.’s whole-brain computational model, the [NeuroMechFly v2](https://pubmed.ncbi.nlm.nih.gov/39533006/) embodied simulation framework, and [Özdil et al.’s](https://www.biorxiv.org/content/10.1101/2024.12.17.628844v1) research on centralized brain networks underlying body part coordination, this demonstration integrates Eon’s connectome-based brain emulation with a physics-simulated fly body in [MuJoCo](https://mujoco.org/). The result: multiple distinct behaviors driven by the emulated brain’s own circuit dynamics. Sensory input flows in, neural activity propagates through the complete connectome, motor commands flow out, and a physically simulated body executes the output, closing the loop from perception to action for the first time in a whole-brain emulation.

This is a qualitative threshold, not an incremental one. Prior work in this space has either modeled brains without bodies or animated bodies without brains. DeepMind and Janelia’s [recent MuJoCo fly](https://www.nature.com/articles/s41586-025-09029-4) used reinforcement learning, not connectome-derived neural dynamics, to control a simulated body. *[C. elegans](https://en.wikipedia.org/wiki/Caenorhabditis_elegans)* projects like [OpenWorm](https://openworm.org/) have attempted embodiment but with far smaller nervous systems (~302 neurons) and limited behavioral repertoires. No one has previously demonstrated a complete emulated brain, derived from a biological connectome, driving a physically simulated body through multiple naturalistic behaviors.

The implications cascade upward. Eon’s mission is to produce the world’s largest connectome and highest-fidelity brain emulation, targeting a complete digital emulation of a mouse brain and laying the groundwork for eventual human-scale emulation. A mouse brain contains roughly 70 million neurons, 560 times the fly’s count, and the team is currently amassing the connectomic and functional recording data needed to attempt it, combining expansion microscopy to map every neural connection with tens of thousands of hours of calcium and voltage imaging to capture how those networks activate in living tissue. If a fly brain can now close the sensorimotor loop in simulation, the question for the mouse becomes one of scale, not of kind.

Watch the video closely. What you are seeing is not an animation. It is not a reinforcement learning policy mimicking biology. It is a copy of a biological brain, wired neuron-to-neuron from electron microscopy data, running in simulation, making a body move. The ghost is no longer in the machine. The machine is becoming the ghost.

Eon is scaling its team and infrastructure to attempt the mouse and human brains next. Those who want to follow or support that effort can learn more at [eon.systems](https://eon.systems/).

*(Disclosure: I have a financial interest in [Eon](https://eon.systems/).)*
