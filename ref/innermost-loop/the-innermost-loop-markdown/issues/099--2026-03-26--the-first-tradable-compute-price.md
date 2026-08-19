---
schema_version: 1
edition_number: 99
title: "The First Tradable Compute Price Index"
newsletter_title: "The Innermost Loop"
newsletter_id: "7404871891775025153"
linkedin_newsletter_url: "https://www.linkedin.com/newsletters/the-innermost-loop-7404871891775025153/"
author_name: "Dr. Alex Wissner-Gross"
issue_date: "2026-03-26"
issue_date_basis: "published_at"
published_at: "2026-03-26T12:39:29+00:00"
modified_at: "2026-03-26T12:39:29+00:00"
source_url: "https://theinnermostloop.substack.com/p/the-first-tradable-compute-price"
source_mirror: "Author’s official Substack publication"
language: "en"
description: "The Singularity has been financing the largest infrastructure buildout in history without a standard price for GPU compute, until now."
cover_image_url: "https://substackcdn.com/image/fetch/$s_!ZxPh!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd00d243b-f701-426e-9158-68b0b8496f90_3264x1312.jpeg"
content_kind: "article"
word_count: 749
link_count: 18
image_count: 1
content_sha256: "266b104294d393b2ca7450d740611a563b0b8d3a0d9c6c01ac41adb45a322e31"
captured_at: "2026-08-19T04:29:57+00:00"
---

# The First Tradable Compute Price Index

[![The First Tradable Compute Price Index](https://substackcdn.com/image/fetch/$s_!ZxPh!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd00d243b-f701-426e-9158-68b0b8496f90_3264x1312.jpeg)](https://substackcdn.com/image/fetch/$s_!ZxPh!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd00d243b-f701-426e-9158-68b0b8496f90_3264x1312.jpeg)

The Singularity has been financing the largest infrastructure buildout in history without a standard price for GPU compute, until now.

Nearly [$7 trillion in data-center investment](https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/the-cost-of-compute-a-7-trillion-dollar-race-to-scale-data-centers) is projected through 2030. Alphabet, Amazon, Meta, and Microsoft alone are staking a [combined $650 billion this year](https://finance.yahoo.com/news/big-tech-set-to-spend-650-billion-in-2026-as-ai-investments-soar-163907630.html). But the capital is flowing blind. No lender can efficiently underwrite what it cannot price. No insurer can accurately cover what it cannot benchmark. No investor can reliably mark a position to market. Trillions of dollars of GPU infrastructure are being financed the way venture deals are, on trust, relationships, and proprietary guesswork, when they should be financed the way energy is, on transparent markets.

[Oil](https://www.cmegroup.com/openmarkets/energy/2023/the-40-year-story-of-a-crude-oil-benchmark.html) got a futures market in 1983. [Natural gas](https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.html) got one in 1990. [Electricity](https://www.fortnightly.com/fortnightly/1996/05-0/milestone-year-power-commodity-markets) got one in 1996. Every critical commodity follows the same arc: first it is vital, then it is opaque, then someone builds a benchmark, and the entire financial stack snaps into place above it. GPU compute has been stuck at step two.

The hyperscalers can self-fund their share. But roughly half of that $7 trillion must come from debt markets, infrastructure funds, pension capital, and sovereign wealth, and those institutions do not write checks they cannot hedge. The risks are real and large. A new GPU generation can crater the resale value of the current fleet overnight. A single geopolitical disruption can reshape the entire supply chain cost structure. Inference demand can shift between providers in weeks. Without standardized pricing, none of these risks can be transferred. Without risk transfer, the capital that built every prior generation of critical infrastructure, from pipelines to power grids, stays on the sidelines. The buildout stalls not for lack of demand but for lack of financial plumbing.

That ends today.

[Ornn](https://ornnai.com/), a company I helped form with backing from [021T Capital](https://www.021t.vc/), is publishing the Ornn Compute Price Index (OCPI) on the Bloomberg Terminal: the first compute price index that derivatives reference and settle against, now available on institutional financial infrastructure.

See it on Bloomberg:

The design draws from the commodity compute most resembles: electricity. A GPU-hour cannot be warehoused. It is consumed the instant it is produced, or it is gone. Futures on OCPI therefore settle the way power does, [Asian-style](https://en.wikipedia.org/wiki/Asian_option), averaging the volume-weighted price of executed transactions over the contract period. Separate indices track each GPU type, from H100 through H200 and B200. Regional weighting reflects the geographic reality that an H100 in Northern Virginia trades differently from one in Amsterdam. Ornn built the index on actual cleared prices from live GPU markets, not surveys, not rate cards, not estimates. The company executed the [first-ever compute swap](https://davefriedman.substack.com/p/how-to-control-your-ai-compute-budget) in December 2025. Founded by former quantitative traders and hardware engineers, Ornn is not guessing at what compute should cost. It is measuring what compute does cost.

Once the benchmark exists, the financial stack follows. Forward curves become constructible. Residual value risk becomes insurable in principle. Contracts referencing OCPI are live on [Kalshi](https://kalshi.com/markets/kxh100mon/h100-monthly-price/kxh100mon-26mar31) and [Robinhood](https://robinhood.com/us/en/prediction-markets/technology/events/price-of-nvidia-h100-compute-on-mar-31-2026-mar-05-2026/), with [Architect Financial Technologies](https://www.prnewswire.com/news-releases/architect-financial-technologies-partners-with-compute-index-provider-ornn-to-launch-exchange-traded-futures-on-gpu-and-ram-prices-302666613.html) signed on to list exchange-traded futures. The keystone is in place.

As Peter Diamandis and I argued in *[Solve Everything](https://solveeverything.org/)*, the Intelligence Revolution turns every scarce domain it touches into an abundant one. But abundance at civilizational scale requires infrastructure at civilizational scale. The shale revolution did not begin when the drilling technology was ready. It began when the [financial infrastructure caught up](https://ifp.org/hot-rocks-part-two-how-public-policy-accelerated-the-shale-revolution/), when lenders could hedge exposure and a futures curve gave capital the confidence to commit. Edison built the generators, but it was [Samuel Insull](https://en.wikipedia.org/wiki/Samuel_Insull) who securitized the revenue streams and turned power into a financeable asset class. Bloomberg Terminal distribution is how a commodity announces it is ready for institutional capital. It is not a data feed. It is a credential. Every commodity that has powered a phase of civilization went through this transition. Compute is going through it now.

Search “ORNNH100” on the Bloomberg Terminal. The most important commodity of the twenty-first century finally has a price the whole market can see.

Those interested in Ornn’s compute pricing and financial products can learn more at [ornnai.com](https://ornnai.com/).

*(This post is for informational purposes only and does not constitute investment, financial, or trading advice. Nothing herein is a recommendation to buy, sell, or enter into any transaction involving GPU compute, derivatives, or any other financial instrument. Statements about future capabilities are forward-looking and subject to uncertainty, descriptions of methodology are not endorsements of accuracy, and past transactions are not indicative of future results. I have a financial interest in [Ornn](https://ornnai.com/).)*
