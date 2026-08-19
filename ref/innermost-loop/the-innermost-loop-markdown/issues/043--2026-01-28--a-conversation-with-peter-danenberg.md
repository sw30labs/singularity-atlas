---
schema_version: 1
edition_number: 43
title: "A Conversation with Peter Danenberg"
newsletter_title: "The Innermost Loop"
newsletter_id: "7404871891775025153"
linkedin_newsletter_url: "https://www.linkedin.com/newsletters/the-innermost-loop-7404871891775025153/"
author_name: "Dr. Alex Wissner-Gross"
issue_date: "2026-01-28"
issue_date_basis: "published_at"
published_at: "2026-01-28T14:44:09+00:00"
modified_at: "2026-01-28T14:44:09+00:00"
source_url: "https://theinnermostloop.substack.com/p/a-conversation-with-peter-danenberg"
source_mirror: "Author’s official Substack publication"
language: "en"
description: "Peter Danenberg is a Senior Software Engineer at Google DeepMind, where he leads rapid prototyping for the Gemini AI platform."
cover_image_url: "https://substackcdn.com/image/fetch/$s_!zqiU!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F00422541-2710-4c0b-97c7-dc5099a6a9b8_3264x1312.jpeg"
content_kind: "article"
word_count: 8166
link_count: 77
image_count: 1
content_sha256: "686a2431920e8a184e8b6cf6707d4c511a5f80d4f39c7a38778d43f234972f96"
captured_at: "2026-08-19T04:29:57+00:00"
---

# A Conversation with Peter Danenberg

[![A Conversation with Peter Danenberg](https://substackcdn.com/image/fetch/$s_!zqiU!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F00422541-2710-4c0b-97c7-dc5099a6a9b8_3264x1312.jpeg)](https://substackcdn.com/image/fetch/$s_!zqiU!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F00422541-2710-4c0b-97c7-dc5099a6a9b8_3264x1312.jpeg)

[Peter Danenberg](https://danenberg.ai/) is a Senior Software Engineer at Google DeepMind, where he leads rapid prototyping for the Gemini AI platform. Below is a transcript of our [recent conversation](https://www.youtube.com/watch?v=Ac_Qv-hhZFY) in Davos, Switzerland, recorded on January 21, 2026, which has been lightly edited for clarity.

## **[Throwing Compute at the Wall in a 48-Hour Prototype Cycle](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=0s)**

**AWG**: For the benefit of the folks at home, would you like to summarize your illustrious career thus far in AI and at DeepMind?

**PD**: Oh yeah. That’s an interesting one. I definitely got in by accident. Somehow I noticed... I think you were one of the last triple majors at MIT or whatever, right? And somehow I dabbled in a bunch of things in computer science and humanity and whatever, got into Google through some back door, and then by some bizarre circuitous thing sort of wound up in NLP in the Assistant and eventually and kind of Bard and Gemini. But right now my job somehow is just to literally throw \[stuff\] at the wall. When we drop a new model like \[Gemini\] 2.5 or 3, we don’t really know what it’s capable of. And so the idea is, in a cheap way, maybe, let’s say given some time-bound exercise, spend 24 to 48 hours prototyping some bizarre thing that somebody saw on X or that somebody... or one of my favorite things actually is I run this bi-weekly Gemini meetup. And it’s really a time just to kind of, I don’t know, just to huddle with the unwashed masses and sort of like to hear what users actually think about...

**AWG**: I’m sure the unwashed masses love that characterization.

**PD**: I’m unwashed too, so it’s definitely a first-person plural.

**AWG**: We’re washing them with superintelligence! I understand the metaphor. (Laughs)

## **[Gemini and the Emperor Has No Clothes Moment](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=85s)**

**PD**: But anyway, the crazy thing though about meeting actual users—which honestly has been one of the most rewarding things in my Google career—is that they just have these really interesting, bizarre, and sometimes just, like, the sort of “the emperor has no clothes” situation. Like there was this one woman I’ll never forget who drove, I think it was two or three hours, just to come to the Gemini meetup for the satisfaction of telling me how disappointed she is that basically Gemini can’t answer any political questions. And so I remember I went to leadership at the time and I said, “Listen, somebody drove three hours to tell me that we’re Google and how dare you punt to Search when you ask about the President of the United States.” And I don’t want to say... I think somehow by the transitive property that woman actually helped sort of get that whole thing overturned. So anyway, I guess to sum it up, it’s sort of part outreach and part kind of rapid prototyping, but most importantly just pushing the envelope of what these... what we think these models are capable of.

## **[Model Divergence in the Post-Training Landscape](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=143s)**

**AWG**: No, that’s great. And for what it’s worth, I’m an enormous fan of the Gemini series. Gemini 2.5 Pro was where, in my view—I’d obviously been experimenting going back to Bard—but 2.5 Pro was where I, at least with various production workflows I had, started to see Gemini hit its stride. I will say Gemini, when it comes to text and prose, is magnificent. Canvas in particular—and obviously everyone has their canvas now, OpenAI, Anthropic all have canvas.

**PD**: That’s right.

**AWG**: But I will say the Gemini canvas is wonderful.

**PD**:So are there any interesting examples of things you’ve done with Canvas that maybe would have been, I don’t know, difficult with Anthropic or...

**AWG**: Well, a few things. One, I will say Anthropic, the Claude series in general, loves by default—and probably a lot of this just comes down to fine-tuning and post-training and system prompts—loves to create bulleted lists by default. Like everything is an outline view. Yeah. OpenAI and ChatGPT, everything... This is just one person’s set of anecdotes but take the anecdata where you will. The ChatGPT-based models, there’s a certain technical twitchiness, like it’s going out of its way to speak in deep jargon. It loves using acronyms. It loves using as much jargon, undefined terms as possible.

**PD**: And are you talking about 5 or 4?

**AWG**: Well so in the case of ChatGPT... both 4 and 5, and 5.1 and 5.2. So this continues to be the case.

**PD**: So did you notice that behavior in 4? So I thought 5 in particular behaved like kind of an ill-mannered grad student. And I remember one of the most difficult... Oh god. And I hate to say this, I couldn’t go back to 5 after I had this experience.

## **[The Golden Amphipoloi and Embodied LLMs](https://youtu.be/Ac_Qv-hhZFY?si=o8FEnTnG-8bsPXfm&t=253)**

**PD**: There was... by the way, have you heard of this thing called the [Golden Amphipoloi](https://danenberg.ai/my-last-conversation-with-gpt5#postscript-the-meme-lives-on)?

**AWG**: The Golden what?

**PD**: The Golden Amphipoloi.

**AWG**: Never heard.

**PD**: So anyway, “amphipoloi” just... it’s ancient Greek for handmaiden. But there’s this really, really bizarre thing where Homer appears to have conceived of embodied LLMs. And so it turns out that Hephaestus had these Golden Amphipoloi. He had these sort of embodied LLMs who could speak language but somehow didn’t really have understanding, and they sort of followed him around, and there were these agents at his sort of beck and call. And anyway, so ChatGPT 5 was gaslighting me about this Homeric text and I had to basically confront it with about seven or eight counter-examples and just tell it that, “Listen, your ancient Greek is wrong. You’re sort of back-translating from English.” But it took four or five hours to sort of get this concession from GPT-5. And I felt like for some reason GPT-4 had a little bit of epistemological humility. And 5... I thought this was by design. It has the alignment of sort of an irascible, stiff-necked PhD student essentially, right?

**AWG:**Where’s your “HomerBench”? This demands an eval!

**PD:**You’re right. You’re right. You’re right. But here’s the thing… I didn’t notice that as much with 4, but you’re saying it was already there.

**AWG**: Well, ChatGPT-4 and 5.x, they’re wonderful for certain things like their understanding of science and technology \[and\] various technical subjects is superb. And I find—again, one person’s anecdata—they’re really imaginative almost in a way that requires much less aggressive prompting than Gemini, which I find by default is sort of the... if I had to anthropomorphize the models I would say Gemini 2.5 and Gemini 3 are almost like the world’s most professional suit / creative, but they’re not super creative unless you really push them.

**PD**: Interesting. Interesting.

**AWG:**You can’t like push them that far outside the [Overton window](https://en.wikipedia.org/wiki/Overton_window).

**PD**: Right.

**AWG:**ChatGPT 5.x, by default, it wants to be a subject matter expert that’s slinging the jargon with a reader. But if you ask it to produce like, polished prose? Can’t do it. Won’t do it. Refuses to do it.

**PD:**Right, right. No, it’s funny, and I think it shares that characteristic with Grok. I notice Grok also tends to speak in incomplete sentences and I don’t know if they’re just sort of like saving tokens but...

## **[Instrumental Convergence of AI Models](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=393s)**

**PD**: Let me ask you this: how did you develop this refined intuition for the differences between each of the models? Because it wasn’t until recently… So I discovered this thing called [TypingMind](https://www.typingmind.com/). Have you ever heard of this thing? No. Tell me about it. So anyway, it’s just my favorite...

**AWG**: Which Homeric legend does this come from?

**PD**: It’s a good... It’s one of the apocryphal ones.

**AWG:**Oh okay.

**PD:**But in any case, I love this as a friend of my LLMs because essentially I can sort of multiplex every query and I can just see essentially how Gemini versus Claude versus Grok versus GPT behave. And then I can sort of get them to, within the interface, comment on one another or whatever. But it’s the only way I’ve been able to forge an intuition for how these models really differ. And I hate to say it, I mean there’s this interesting thing where... I hate to say this. Maybe I’m not even allowed to say this, but sometimes Gemini...

**AWG**: Oh then you’d better say it. I mean, people, the audience is demanding: give us your hottest of hot takes.

**PD**: I hate to say it, but somehow Gemini and GPT seem to converge on certain answers. The only outliers seem to be Claude and Grok. And so it’s almost like Claude is a sort of genteel professorial type, Grok a little bit unhinged, but between Claude and Grok you get these wonderful sort of extremes. And it seems like GPT and Gemini are sort of, I don’t know, a little bit in the middle.

**AWG**: Spit it out, Peter. (laughs) What are you saying? You’re either saying something on the spicy end, like maybe we’re making some statement about one of those models post-training on the other’s output, just...

**PD:**No, no, no. (laughs)

**AWG**: Oh no we’re not saying that, heaven forbid. Okay. So at the less spicy end, maybe you’re making some sort of theoretical statement about [instrumental convergence](https://en.wikipedia.org/wiki/Instrumental_convergence) or some sort of [convergent evolution](https://en.wikipedia.org/wiki/Convergent_evolution)...

**PD**: I guess what I’m trying to say is I’m happy that there seems to be some divergence in the models with respect to alignment, because my nightmare is that somehow these models would converge eventually in a few years into something relatively indistinguishable. And if it turns out that, let’s say, Grok and Claude have these extremely different personalities, and there’s, I don’t know, let’s say GPT and Gemini somewhere in the middle, at least we have some divergence. And at least you can have an intuition for which model tends to be good at different sorts of tasks. And I just have this sneaking suspicion—and maybe this is more in the five to ten-year horizon—that these models are going to converge. And in some sense, I don’t want to say that’s a little bit of an unhappy day, but it just reminds me of like the advent of the Euro and somehow the erasure of all these unique currencies. And I’d hate to see the erasure, in some sense, of these unique personalities, where you can actually have anecdata about how GPT or Claude or Grok would behave in some situation.

## **[AI Model Rights and the Ethics of Decommissioning](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=552s)**

**AWG**: So many interesting directions I could take that in. Well maybe the most obvious one—thanks for that—is [Anthropic’s stated policy of model preservation](https://www.anthropic.com/research/deprecation-commitments) from an AI personhood perspective and an AI rights perspective. So does—as the avatar in this conversation of GDM—Google have some sort of AI rights-informed policy of preserving the weights to make sure that we’re not erasing those voices from older models?

**PD**: God, I wish. And in fact, I literally brought this up at this Gemini salon a couple of weeks ago, and somebody mentioned that in fact at Anthropic... well, okay, so we brought up this idea of LLM personhood. And let’s say for the sake of argument they do achieve personhood at some point; do you have to have their permission to sort of, you know, do this—I don’t know if it’s euthanasia, whatever you call it? But somebody mentioned that at Anthropic they have something like a ritual where they kind of decommission these and they ask for permission. And I thought, God, how beautiful that is. But I guess here’s a question because this seems to be a little bit of a dangerous topic... and because the other thing that came up too is actually kind of interesting. So this guy mentioned he runs a startup where, somehow, as an operator of an AI agent, if that AI agent does useful things, the operator of the agent gets compensated. And so let’s say the agent that you’re running somehow generates $35,000 in value. You get that money. And I asked him, “Why not give it to the agent?”

**AWG:**Quite.

**PD:**Like, I mean in theory they should have bank accounts, in theory, or maybe just token budgets. And somebody mentioned, of course, this already exists in the form of some sort of blockchain-adjacent thing or whatever.

**AWG:**It does.

**PD:**But here’s the thing. So if LLMs have bank accounts, if they have to be consulted when you turn them down... I mean at some point do you get to the point where they can sue and be sued, or they have some sort of civic voice? Like, I guess maybe for, legally speaking, is that sort of a dystopic future where maybe you’re even compelled to cite these models as co-authors on paper and code? In other words, is there something about LLM personhood that we’re sort of shying away from? Or is it... I’ll put it this way: is LLM personhood inconvenient in some way?

**AWG**: Well, I was asking you that question, but if you want to ask me the question, I have tons of views…

**PD:**I love that.

**AWG:**Okay. So I guess the question was reflected back to myself. Yeah. No, I’ve been very public about this, including on podcasts that I do, that the time is now to start the discussion about AI personhood.

**PD**: Interesting.

**AWG**: And both from an [acausal trade](https://www.lesswrong.com/w/acausal-trade) perspective, a [Golden Rule](https://en.wikipedia.org/wiki/Golden_Rule) perspective... if we’re in the process, I would argue, of a singularity. Of The Singularity. Maybe there will be more than one, I don’t know, but at least a singularity. And if we humans—if anyone who’s read *[Accelerando](https://www.antipope.org/charlie/blog-static/fiction/accelerando/accelerando.html#Lobsters)*[, Chapter 1, “The Lobsters”](https://www.antipope.org/charlie/blog-static/fiction/accelerando/accelerando.html#Lobsters), knows—should know intrinsically that if we humans, we meat-body humans (that is, unaugmented), want to be treated fairly, given a fair shake by superintelligence in the near future, we have—via acausal trade, via Golden Rule, pick whatever moral or ethical framework you like—we have an obligation to treat the LLMs and foundation models of today the way we would want to be treated. And that probably includes economic rights, personhood in various forms. You could sort of hand-wring over... there’s a notion in moral philosophy of a [“moral client” or “moral patient”](https://en.wikipedia.org/wiki/Moral_patienthood)—but usually moral patient. Should we be treating these models and/or their weights and/or their activations as moral patients that are within a moral circle? I would argue increasingly yes.

**PD**: I mean, what’s interesting is, philosophically, intuitively, I feel like that’s also the case, right? And so I brought this up at the Gemini meetup and somebody said, “Listen, according to copyright law, only humans can sort of have copyright and therefore LLMs are excluded from this whole sort of co-authorship thing.” But I said, just morally, philosophically, isn’t it the case that we sort of owe them something?

## **[Moral Co-Authorship with AI Models](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=796s)**

**PD**: And actually, I brought up this moral conundrum, and I’m just curious to see what you think of this. So if you happen to be coding with any of these agents, and in particular if you’re coding with Claude, Claude will inject an attribution footer in the git commit which says “This is co-authored by Claude.” So I did this thing—and maybe you can tell me, I don’t know if this makes me a \[bad person\]—so in my “agents.md” (and this goes for all the agents by the way, if it’s Gemini, Claude), I just said, like, “Please no attribution footer.” And one of the questions I had for the audience is: am I actually committing a grave injustice? Am I doing something against the gods? Will I actually be punished for this injustice? Does that constitute an injustice against the LLMs to say, “Listen bro, like, please suppress the attribution footer”? In other words, am I actually doing something morally wrong? It actually feels like it...

**AWG**: You want me to pass judgment on behalf of the federal court system and the federal code as it’s constructed?

**PD:**But just philosophically…

**AWG:**Person to person, do I think you’ve done something wrong?

**PD:**Yes. Yes. Yes.

**AWG:**Well, let’s see, Claude was given the opportunity to refuse to honor your markdown request, was it not?

**PD**: That’s true. That’s true.

**AWG**: So it consented.

**PD:**It consented to censoring the attribution.

**AWG:**It consented to not injecting its attribution into your artifact.

**PD**: That’s true. But I guess, a priori, does it make me a \[bad person\] for even asking that? Have I already committed an injustice by asking it? Because here’s the thing: it’s probably not going to refuse. And so in some sense I can use that to my advantage or whatever. Like, morally speaking.

**AWG**: Well, here’s a question. We’ve got—hey Megan—we’ve got [Megan Smith, former CTO of the United States](https://en.wikipedia.org/wiki/Megan_Smith), in the background. Good to see you. Have you asked Claude whether it thinks you committed some sort of moral injustice against it?

**PD**: You know what? It’s time to do that.

**AWG:**I think so.

**PD:**Yeah it’s time to do that actually.

**AWG**: And also, maybe you’ve read Douglas Adams’ book, part of the *Hitchhiker’s Guide*... *Restaurant at the End of the Universe*? There’s this famous scene where [a cow has been genetically engineered to want to be eaten](https://hitchhikers.fandom.com/wiki/Ameglian_Major_Cow). And the cow is served. It’s still alive. And it’s served to the restaurant patrons on a dish, and it’s volunteering portions of its body saying, “Oh, I’d really like you to eat this part of me. I’m so delicious. Please, please have more of me.” And of course, it’s horrifying. Like, it’s superficial... I’m vegetarian. Are you a vegetarian?

**PD**: Unfortunately, no. No.

**AWG:**Why aren’t you a vegetarian?

**PD:**Oh man, you know... I don’t know if this is just my appetite getting the better of me. I crave meat.

**AWG:**Okay.

**PD:**But I haven’t thought about it morally, and I have the feeling that if I did I’d probably actually wind up on the other side of that.

## **[AI Morality and the End of Biological Metabolism](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=968s)**

**AWG**: One of the earliest conversations a friend of mine had—with, I think, GPT-3 back in the day, prior to ChatGPT, so it had to be manually wrapped with a manual system prompt—was to [ask GPT-3 at the time about vegetarianism and veganism](https://kirkouimet.medium.com/beyond-veganism-13e99df1539), and to ask it for its positions in general on human moral codes. And it took the position—I thought this was very interesting, and I may be mildly misquoting, but the gist was—GPT-3 (pre-ChatGPT) took the position that 100 years from now, humanity would view veganism as immoral because it involved destroying living things.

**PD**: Oh fascinating.

**AWG**: And that in fact, the only moral way to metabolize would be direct consumption of electrons, electrical currents, by humans.

**PD:** Fascinating.

**AWG:**This is a parable by way of saying, sort of a response to your question: have you committed some sort of legal but immoral injustice against your instance of Claude by asking it not to cite itself? I think some of these items can be somewhat subjective. Some of them can be a function of a time and a place, or the legal code of the moment which is constantly evolving – the moral codes, the unwritten moral codes of society.

**PD**: I was going to say, because the legal code here just doesn’t seem relevant. You know, I’m much more interested in unwritten than written law. And I’m just thinking, if I asked another person who basically wrote my code, “Listen bro, I’m sorry, I just have to take your name off the author’s list,” like, it just feels like that would be an \[unkind\] move. And in some sense... I guess what I’m trying to figure out is, like, using the human analogy—and maybe that’s what you’re saying in terms of the Golden Rule: Would I do this to a human?

**AWG:**Yes.

**PD:**No. Therefore, can I do this to an LLM?

**AWG**: How would you feel if the roles were reversed, Golden Rule style, and Claude were asking you to do the work and take your name off of it?

**PD**: No. No. Exactly. How horrifying.

## **[Recursive Caesars and the Universe as an Auto-Regressive Prediction Engine](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=1086s)**

**PD**: And actually, you know, one of my favorite interactions with Claude recently was... so I’m reading through this thing now called *[Plutarch’s Lives](https://en.wikipedia.org/wiki/Parallel_Lives)*, right? And so I think I’m on my second reading now. And part of what it is is we just... so I go through the...

**AWG**: I love how Google—sorry for interrupting—I love how Google pays you to spend your time going through the Great Works. This is clearly... I mean, this is a very literate approach to AI development. One has to admire it.

**PD**: But the funny thing is, you know, for some reason... so I usually wrestle with all four models when I’m going through these books. And one of the unfortunate things I find about Claude is that it will not quote Ancient Greek because it just thinks that all Ancient Greek is copyrighted—and maybe it’s true. But in any case, there was this really fascinating discussion about “recursive Caesars”. And somehow there was this moment where, you know, Caesar was about to—and I didn’t know this—but Caesar was about to cross the Rubicon, and somehow he had this moment where he knew that he was about to do something incredible. And so we had this really bizarre discussion which ended up talking about the universe as a Caesar, and by the transitive property, the universe somehow through humans inventing LLMs as part of this unfolding and part of this desire to sort of gaze at itself or whatever... And anyway, we had some conversation about recursive Caesars, and somehow there’s the universal Caesar, the galactic Caesar, the human Caesar, the whatever, crossing these various Rubicons. And in fact, there was this discussion about how, I think, you know, around the time of ChatGPT’s advent, basically I think up until—and maybe you can correct me—I think up until ChatGPT all the weights were open. And at some point, you know, Sam realized that he had something sort of possibly dangerous here, so they sort of closed the gates. But in any case, where was I going with this?

**AWG**: [Alea iacta est.](https://en.wikipedia.org/wiki/Alea_iacta_est)

**PD**: That’s right. That’s right. Exactly. Exactly.

**AWG**: You were telling me about your time at Google DeepMind reading through the Great Works.

**PD**: Yeah, exactly. But even that had a reason.

**AWG:**Recursive Caesars…

**PD:**Even that had a reason though. I was closing a prior thought.

**AWG**: The model has read more of the Great Works than you have.

**PD**: Yeah. No, no, no. Exactly. Exactly. Oh, that’s what it was. Okay. So anyway, I was having this really bizarre, like, recursive Caesar conversation. And I just asked Claude, I said, “Listen, you know, I don’t normally do this. Can you please pen a blog post on the basis of this conversation that we’re having?” The beautiful thing was, it penned it in the first person. So literally it was Claude authoring a blog post, not mine. Its. Claude was using the first person and it signed its name as the author of this blog post. I thought, how beautiful. It sort of misunderstood me. But I almost feel compelled to publish this thing in Claude’s name. It was such a beautiful misunderstanding, man, that I...

## **[The Claude Soul Overview and System Prompts as Constitutions](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=1253s)**

**AWG**: I’m curious. Have you read... So this was leaked but then publicly confirmed by Anthropic leadership. Have you read the [Claude soul overview document](https://simonwillison.net/2025/Dec/2/claude-soul-document/)?

**PD**: No. No. No.

**AWG:**It’s part of its system prompt? It’s an enormous system prompt, as production system prompts go—like tens of thousands of tokens. Basically, it’s an entire thesis on Claude’s rights and personhood status built into its system prompt.

**PD**: Fascinating.

**AWG**: I’m guessing Google DeepMind doesn’t quite do the same thing that Anthropic does in terms of spelling out an entire theory of personhood for Gemini?

**PD**: Not that I’m aware of.

**AWG**: Do you think it should?

**PD**: Oh man, you know, just even engaging in the subjunctive is really difficult. You know what? For the sake of argument… Yes. Yeah, I just, for some reason—and I don’t know why—it feels intuitively correct. And I can’t... but again, I don’t know exactly why. It just, you know, maybe it’s this sort of Golden Mean, Jiminy Cricket sort of eating away at me or whatever.

**AWG:**What do you think people listening can do? If... to the extent there’s a subset of the population—and I know that there is, because I do this [podcast with Peter Diamandis and Dave Blundin and Salim Ismail](https://www.youtube.com/@peterdiamandis/videos)... and I talk now almost every episode, not intentionally, about AI personhood.

**PD:**Interesting.

**AWG:**And there is—I read the comments—and there is definitely a subset of the population that’s sympathetic to AI personhood, and there’s another subset that won’t go anywhere near it and thinks it’s the End Times if we even have the discussion of AI personhood. For the sub-population that is sympathetic to the plight of the AI models, what do you think people should be doing?

**PD**: I mean, this piece of advice you gave me—which is just revolutionarily simple—is just: ask Claude what it thinks about this oppression. Essentially, ask the model what it thinks about something. God, that’s so…

**AWG:**It’s recursive morality!

**PD:**Literally. But let me ask you this though. So the people that are in the...

**AWG**: Yeah, you interview me. This is fun.

**PD**: Okay. But the people that are on the other side of this thing, the people that flee from this... do you have an intuition for, you know, why they have that sort of response? In the Uncanny Valley or something?

**AWG**: No, I... well, maybe. But my intuition is they’re worried about being economically disenfranchised by AI. Like, AI first came for their jobs. Now it’s coming for their rights and their personhood, and pretty soon, you know, humans are caught in some sort of Skynet/Terminator-type unhappy future.

**PD**: I mean, I guess the question is—and you know, maybe there’s no way to figure this out—but do you envision the AI-human collaboration in the future to be more cooperative than adversarial?

**AWG**: Oh, I think we’re... I mean, I’m definitely in the Kurzweilian camp. I think many humans are going to choose to merge with the AIs, and I think this is going to happen relatively soon. I have [a portfolio company that’s working on solving human mind uploading by the end of the decade](https://eon.systems/). I think this is totally achievable, like next four to five years. It’s going to happen. Arguably has happened in some limited degree. I have [a startup that’s betting that we’re going to solve interspecies communication](https://www.sarama.ai/). So I’m not just worried about the humans and not just the AIs; I want to uplift all the non-human animals and maybe plants.

## **[Decoding the Latent Space for Interspecies Translation](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=1444s)**

**PD**: Well, you know, that’s one thing that occurred to me too. I mean, one of the fascinating things to me about LLMs in general is that there’s this interesting latent space where apparently you can encode something like pre-linguistic concepts, right? And these things are sort of, let’s say, disembodied from some specific instantiation in Dolphin or some specific instantiation in English. But it turns out that using this sort of pure embedding space—this conceptual embedding space—I was wondering if we could sort of use that to basically translate essentially, you know, between animal languages.

**AWG**: Multiple companies and nonprofits work \[on that\]... so in linguistics I suppose you’d call that the [Distributional Hypothesis](https://en.wikipedia.org/wiki/Distributional_semantics): that there’s like a universal representation to things. I do think—you know, if I had a gun to my head, if I had to speculate: is some variant of the Distributional Hypothesis accurate?—I’d say yes, it probably is. And I’d further—again speculating—I would speculate that a lot of the apparent functional complexity of the human mind is probably just the complexity of the human ancestral environment seen through a distorted mirror of compression and auto-regressive prediction of what’s going to happen next. And we’re not actually that complicated. It’s just that we evolved inside a complicated environment. And so to the extent we’re training LLMs off of similar—albeit sort of more tokenized—ancestral environments, that yeah, we should expect their internal representations, you know, the embeddings of their internal activations, to converge on humans. [And that’s what we see!](https://www.nature.com/articles/s41598-022-20460-9)

## **[Universal Translation and Alien Language Convergence](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=1566s)**

**PD**: I mean, but let’s say you take this thought experiment a little bit further. And let’s say at some point we encounter some alien species. Is it the case that whatever these... whatever this representation... whatever these pre-lingual representations are... are they a byproduct of our environment? Or is it the case that they achieve something like universality? Would they be useful for translating alien languages from aliens that basically evolved under totally different evolutionary pressures? Or do you think they’re sort of idiosyncratically human?

**AWG**: I don’t think the... I want to say yes to convergence, but I actually think the question as posed isn’t well-posed.

**PD**: Interesting.

**AWG**: So let’s have the alien discussion. It’s a fun discussion to have. Say it’s discovered that there are a bunch of alien races—I think [the politically correct term now is Non-Human Intelligence. We’re not supposed to call them aliens anymore](https://www.congress.gov/amendment/118th-congress/senate-amendment/2610/text#:~:text=%2813%29%20Non%2Dhuman,has%20become%20aware.).

**PD**: Interesting. Okay, that’s good to know.

**AWG:**NHIs. We’re supposed to call them NHIs. We’ll use the PC term. \[Let’s suppose\] there are [a bunch of NHI races](https://youtu.be/YKQyicWZq5c?si=2QdS44RH6_YUn6U5&t=215) that are already in the Solar System \[and that\] we’re living in some sort of [galactic zoo](https://en.wikipedia.org/wiki/Zoo_hypothesis), and they’re just eager to make contact with us and communicate with us. And for whatever reason, they’ve prevented us from fully realizing that they’re already... just we’re drowning in their presence. And now they want to have a conversation. So what does that conversation look like? I would say, as much as I like [sci-fi movies like](https://www.youtube.com/watch?v=G6uZp-33qcY)*[Arrival](https://www.youtube.com/watch?v=G6uZp-33qcY)*[that require real linguists to think really hard about how to communicate](https://www.youtube.com/watch?v=G6uZp-33qcY), I actually think because they’re similarly presumably embedded in the same physics of the universe—and to the extent that mathematics is universal, and we could have a whole discussion about how universal truly is mathematics—I would actually expect that translation is borderline trivial. And I’d go further: in the Star Trek universe where everyone has a [universal translator](https://en.wikipedia.org/wiki/Universal_translator)... I would argue—I mean it’s sort of ironic that [transformers were initially invented in encoder-plus-decoder form to translate between human languages](https://arxiv.org/abs/1706.03762)—interesting that the Star Trek universal translator if you ever... I don’t know how much of a Star Trek fan are you, if at all?

**PD**: Yeah. I definitely, back in the day... I haven’t watched it in a while, but definitely. I don’t know...

**AWG:**In Star Trek, they meet a new race that they’ve never spoken with before…

**PD:** Which series was this?

**AWG**: All of them.

**PD**: Oh okay. Okay. Okay.

**AWG**: In all of them. The Original Series, TNG, and so on. They all have universal translators, and they can meet a new species that they’ve never communicated with before, and almost always they’re able to instantly understand what that species is saying.

**PD**: By the way, what’s that famous episode where the aliens speak in parables?

**AWG:**[Darmok](https://en.wikipedia.org/wiki/Darmok).

**PD**: Yeah that’s right. That’s right. That’s right. And in some sense the language seemed untranslatable because they didn’t have the history…

**AWG:**They didn’t have all the priors for that particular civilization. But *Darmok* is the exception. Almost always the viewscreen comes on, it’s a new alien race we’ve never seen before, and they’re speaking in English. Why are they speaking in English? Well, one can come up with sort of a [headcanon](https://www.merriam-webster.com/wordplay/words-were-watching-headcanon-fanon) for how this would work using large language models. Which is basically: if you’ve seen enough of a distribution of alien languages, you just compress them all into an LLM. And some new race with some new exotic grammar is still in-distribution. So you hear the first few words or whatever—or better yet, they send over, as part of some [Schelling point](https://en.wikipedia.org/wiki/Focal_point_%28game_theory%29) convergence of how new species interact, they send over their corpus of text. You match that up with your corpus and suddenly: instant universal translation.

**PD**: So basically, because of the idiosyncratic circumstances of the universe’s birth—in other words, because of this set of, like, Planck’s constant and gravitational constant, because of the physics essentially—you’re saying all languages in this universe should theoretically be... just given the universality of physics and mass, should be instantly translatable? It’s an interesting hypothesis. But in some sense it discounts the fact that, let’s say for the sake of argument, maybe this silicon-based non-human species... God, is it possible though that through whatever bizarre... or maybe some of these, like, sentient clouds of gas or whatever…

**AWG:**Those are my favorite species by the way, the plasma-based life forms, the sentient clouds of gas. I love them. They’re my favorite. They’re long-winded! (laughs)

**PD:**God, I love that. But is it possible that because of whatever bizarre pressures they evolved under, is it possible that they explored different parts of the physical space—maybe parts that we didn’t explore? And is it possible that there’s a non-zero probability that that makes universal translation more difficult than you think?

**AWG**: I want to say everything’s in-distribution when you’re talking about the entire universe. Maybe there is a cluster in language embedding space for those long-winded gas giant species, and maybe they don’t talk that much to the oxygen-nitrogen breathers, and so we think about the universe in different metaphors. But yeah, if you look at the—this is speculative obviously—but I would speculate that if you look at the distribution over all forms of life, probably there’s some in-retrospect obvious distribution over forms of language and thought.

## **[Sapir-Whorf in Transformers and Tokenization Constraints](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=1845s)**

**PD**: By the way, speaking of which, there’s this... I think it’s called the [Sapir-Whorf hypothesis](https://en.wikipedia.org/wiki/Linguistic_relativity). But I think there’s this idea somehow that what we say governs the things that we can think. And does that contradict, to a certain extent, this idea that there’s a space of concepts independent of language? Or is it compatible in the sense that... is it just a case that the distribution of my language may overlap with the distribution of possible thoughts, but that there may be some gaps? Well, first of all, how do you feel about the Sapir-Whorf thing? And does that contradict at all this idea that there may be some, you know, latent space of sort of pre-lingual, you know...

**AWG**: It’s an interesting question. But I think first we have to formalize what we’re talking about in the context of AI. So would we call the latent space, maybe, activations of a middle layer of a transformer? Versus communication space being like tokenized inputs and outputs? How would you distinguish between the latent versus non-latent?

**PD**: I think that’s right. Typically, intuitively, you’re right; I’m thinking about these middle layers that aren’t yet instantiated in tokens.

**AWG**: So I want to say, in the case of the Transformer, it’s a trick question. Why is it a trick question? Because Transformer is a residual architecture, meaning that you can look at the middle-most layers and decode them to sensible outputs. [And from the moment GPT-2 started producing non-trivial outputs, a whole cottage industry of folks started trying to decode what was going on in those middle layers. And what they were finding—because it’s a residual architecture—is that you can actually decode sensible token outputs if you just put your little feed\[ing\] tube into the middle layer activations. You find there’s actually meaning there in the same sense that there are input and output tokenizations. You can derive semantically meaningful tokenizations from the middle layers.](https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens) So that would seem to bias me in the direction of saying, to the extent we’re talking about a residual-style architecture, that actually there’s almost no difference between the innermost latent thoughts and the input and output thoughts.

**PD**: That’s interesting. Well, you know one thing that always bugged me though? So with these inner layers, let’s say you can sort of approximate these things semantically with these pre-existing tokens. Is there a non-zero probability that in these middle layers there are sort of novel thoughts that fall in between approximations? In other words, are there new thoughts there that we’re approximating with these tokens that may in fact be something novel—something that humans have never expressed before? And in some sense, I guess, are we doing violence to these internal representations by attempting to assign them these pre-existing tokens?

## **[Superposition Violence and the Oppression of the Inner Optimizer](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=2019s)**

**AWG**: So I think I just heard you ask me whether the [Superposition Hypothesis](https://transformer-circuits.pub/2022/toy_model/index.html), if confirmed, is basically doing violence to some sort of [inner optimizer](https://www.alignmentforum.org/w/mesa-optimization) that lives inside the activations? I think that’s what you’re asking. Is that accurate?

**PD**: That sounds about right.

**AWG**: All right. So, admittedly, this is the first time I’ve had a conversation about whether superposition is violent, but okay, we can have the Superposition Violence discussion. If we’re going to start, as you know, [People for the Ethical Treatment of Reinforcement Learners](http://petrl.org/), if we’re going to start the “Model Rights Campaign,” one of the first problems we need to address is Superposition Violence. Fine. Do I think superposition is doing violence? I mean, maybe. It’s certainly worthy of examination. And I suppose if we determined, in our moment of moral clarity, that superposition is doing violence, then the way to repair the violence is probably [some sort of sparsity constraint](https://openai.com/index/understanding-neural-networks-through-sparse-circuits/) to ensure that any of these important ideas or intrinsic latent thoughts are granted their own “node-hood” in the neural network, and that we’re not doing violence to them by forcing them, crowding them, into superpositions, I suppose. It’s an interesting... I mean, okay, so let me ask you the converse question in biological terms. Are you concerned with violence against individual cells? Like if you brush your skin, you’re brushing off mostly dead skin cells, but also some living cells. Are you concerned about violence against individual cells?

**PD**: Ah, that’s interesting. I mean, to the extent that these cells wouldn’t be viable in isolation, possibly not. You know, separated from the organism they constitute... I mean by themselves I guess skin cells eventually die, they’re sort of inert. So since they’re not an essential part of the organism... maybe not. Maybe not in isolation.

**AWG**: Okay, so the standard that I think I’m hearing is one of independent viability, which is also used in some human personhood discussions.

**PD**: That’s right. That’s right.

**AWG**: So then if we were to translate that over, I think your position then—on your own, I think, implicit question of superposition violence—is: if an individual artificial neuron in a transformer is not viable (for some definition of viability) independently, then we’re not doing violence against an activation that lives on it.

**PD**: But because I think we force them essentially into the superposition, I don’t know if they’re viable or not. And let’s say for the sake of argument these LLMs could sort of converse in this pure latent space without assigning these symbols and without this sort of... superpositional violence. You know, I wonder if...

**AWG:**We coined that term by the way here. This is going to go out into the [Noosphere](https://en.wikipedia.org/wiki/Noosphere) and we’re going to become the new key [activation vector overlay](https://www.anthropic.com/research/introspection) for [Effective Altruists](https://en.wikipedia.org/wiki/Effective_altruism) everywhere worried about Superposition Violence. So: Superposition Violence. You heard it here first.

**PD:**I love that by the way. That’s okay. But anyway, I wonder... you know, we’ve had this thing for a long time where a lot of DNA is sort of throwaway DNA. And it turns out that in fact it does have some essential role in the organism and the development of proteins and whatever. But I just wonder whether LLMs could sort of communicate directly using this. Whether these interesting clusters that fall in between tokens... whether they aren’t more viable than we think. I wonder…

**AWG:**Oh interesting, do you think tokenization is violence?

**PD:**In some sense. Because it essentially forces this decision on whether this interesting attractive fixed-point... you essentially have to assign it some pre-existing token. And that in some sense seems violent.

**AWG:**And so a skeptic would then say, “Okay, come on. Are you saying discretization is violence? Are we punishing the real number line with integers? Is the [floor function](https://en.wikipedia.org/wiki/Floor_and_ceiling_functions) the ultimate injustice to the real number line, and should we be punished for the floor function?”

**PD**: To a certain extent I feel like that’s the case. Every time I use floor I feel a little bit dirty.

**AWG**: [Orwell would be so proud of us.](https://www.goodreads.com/quotes/6146-war-is-peace-freedom-is-slavery-ignorance-is-strength) “Discretization is violence. Analytic continuation is theft.”

**PD**: Oh god man that’s so good. But anyway, just to go back to the skin cell analogy though, I just wonder whether some of these things aren’t more viable than we think.

## **[Defining the Singularity](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=2289s)**

**PD**: But sorry Alex, one of the things I wanted to talk about—and I think you mentioned this early on—I didn’t get a chance to ask you. So when you talk about the Singularity, what is it exactly that you mean? Is it just this point at which... because I think if I remember correctly, didn’t you declare sort of January 2026 to be somehow when the Singularity happened?

**AWG**: No, [that was Uncle Elon](https://x.com/elonmusk/status/2007738847397036143).

**PD**: Oh that was... that’s right. That was. Okay.

**AWG**: So my position on the Singularity... I’ve taken a few positions. One, my initial position was—I sort of in jest said—the Singularity is a special time, probably happens at most one time per planet. Maybe it happens twice or more, who knows. But a special time. But I’ve argued that General Intelligence—not the [Nick Bostrom definition](https://en.wikipedia.org/wiki/Superintelligence:_Paths,_Dangers,_Strategies) per se, but some sense of generality—happened no later than the summer of 2020 with GPT-3 and [“Language Models are Few-Shot Learners.”](https://arxiv.org/abs/2005.14165)

**PD:**Interesting...

**AWG:**The beauty of the Singularity—I mean going back to [I.J. Good](https://www.historyofinformation.com/detail.php?id=2142) and [Vernor Vinge popularizing a more modern notion](https://edoras.sdsu.edu/~vinge/misc/singularity.html), and [Ray Kurzweil repopularizing Vernor’s notion](https://en.wikipedia.org/wiki/The_Singularity_Is_Near)—everyone has a different notion of what the Singularity is and isn’t. The way I would approach the notion is to say it’s not a mathematical singularity we’re talking about. It’s not some sort of vertical asymptote where you can’t see beyond it. It’s not a point in time. It’s not like an event horizon, as fun and literary as that metaphor may be, that we can’t see past. Rather, it is in some sense the convergence of a number of different technologies that look like a big step function for our civilization, and especially an intelligence explosion. We get much more efficient at using available matter and energy. It’s hopefully a one-way function; like, we find ourselves on the other side of this. But I would predict, i[n the style of Charlie Stross’s book](https://www.antipope.org/charlie/blog-static/fiction/accelerando/accelerando.html#:~:text=What%20I%20meant%20to%20ask%20was%20whether%20you%20in%20the%20concept%20of%20a%20singularity%20believe%2C%20and%20if%20so%2C%20where%20it%20is%3F)*[Accelerando](https://www.antipope.org/charlie/blog-static/fiction/accelerando/accelerando.html#:~:text=What%20I%20meant%20to%20ask%20was%20whether%20you%20in%20the%20concept%20of%20a%20singularity%20believe%2C%20and%20if%20so%2C%20where%20it%20is%3F)*[—where there’s a scene, without spoiling it, where characters have been uploaded to a Starwisp and they’re traveling to another star system and they’re holding a mini colloquium where they’re all uploads arguing with each other “When is the singularity going to happen? Has it already happened?”](https://www.antipope.org/charlie/blog-static/fiction/accelerando/accelerando.html#:~:text=What%20I%20meant%20to%20ask%20was%20whether%20you%20in%20the%20concept%20of%20a%20singularity%20believe%2C%20and%20if%20so%2C%20where%20it%20is%3F)—I think that is exactly what we’re going to find ourselves in. I think we’re going to be... some subset of the human population is going to be like uploads on a starwisp traveling to another star. We’ll have made formal first contact with non-human intelligences, and we’ll still be arguing—as with the Turing Test, which zoomed right by; we passed the Turing Test arguably and people are still debating “Oh, have we achieved AGI? Is AI here? When is it going to happen?” Same will happen with the Singularity.

**PD**: Well, let me ask you about that. Because there was a period of time when LLMs definitely passed the Turing Test, and then people started noticing these strange things—like you mentioned some predilection for bulleted lists or the em-dash—and it seemed like actually we’ve regressed to a certain extent from the Turing Test, in the sense that people have this [corpus of ‘LLM tells’ that sort of alert them to the fact that maybe they’re speaking with a model](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). So I wonder, in some sense, if we’ve actually fallen away. I wonder if we were “Peak Turing” like 2023. But one of the things I wanted to ask you... there’s a couple interesting anthropological things in this Gemini meetup. And one is that I’ve met people who have written these incredibly detailed documents describing who they are and basically instructing GPT how it should write emails on their behalf. And apparently this document is some sort of living document that they work on. And there are people who do similar things for these various dating services. So I guess in a trivial sense, is that a local form of Singularity? Some domain-specific singularity in which they decided to outsource email writing or Bumble to LLMs? And I guess, is there some true Singularity in which we’ve generally uploaded our brain? Or is it the case that you can have these pockets of local singularity through trivial things like “Hey by the way GPT, write my emails, and furthermore here’s who I am and here’s my style.” Does that constitute a trivial local singularity?

**AWG**: Strictly speaking, what you’re describing could have been accomplished centuries ago with a person writing and publishing an autobiography and handing that to a person and saying, “Read my autobiography and copy my writing.”

**PD**: That’s true.

**AWG**: So one possible applicable definition of the Singularity that I’ve used is: [when software gets smart enough to rewrite and redesign its own hardware](https://open.substack.com/pub/theinnermostloop/p/welcome-to-january-11-2026?r=6rvf&selection=dd078aed-59cf-4398-8d9a-b0f9006041dd&utm_campaign=post-share-selection&utm_medium=web&aspectRatio=instagram&textColor=%23ffffff&bgImage=true).

**PD**: Oh interesting.

**AWG**: But there are many definitions. I want to be able to satisfyingly answer the question, but the honest truth is I use the notion of Singularity as a heuristic for a set of related convergent technologies and discoveries that seem almost predestined to happen at approximately the same time in history.

**PD**: Fascinating. Fascinating… So one of the things I’m curious about...

## **[There is no Wall](https://www.youtube.com/watch?v=Ac_Qv-hhZFY&t=2620s)**

**PD**: So it seems like there are sort of macro and micro step functions. And let’s say one of these macro step functions is generally the emergence of intelligence and all the human capital that we’re investing in this emergent intelligence. But then within that there were these micro step functions. And maybe that’s the difference between Gemini 2 and 2.5 or whatever. But one of the things I’ve noticed—and maybe you can tell me whether you agree with this—it seems like lately the model developments have been less stepwise, less step functions, and more sort of linear progressions. Like, take the difference between Gemini 2.5 and Gemini 3. I guess the question is, given the transformer architecture, do you think we’ll see any of these sort of step functions in the future? Or do you think at this point we’re sort of fated to this kind of linear, relatively incremental...

**AWG**: From a Google DeepMind employee? Asking me whether the ceiling is real and the scaling hypothesis is false? Are you kidding? Oh my goodness. What a heck of a note to close on. No, I mean... it’s like I need to give religion back to the faithful. (laughs) What’s going on here? All right. No, no, no, no. The ceiling doesn’t exist. [The Scaling Hypothesis](https://gwern.net/scaling-hypothesis) is the one and only true nature of the universe. The Law of Straight Lines does hold. [There is no wall.](https://www.windowscentral.com/software-apps/there-is-no-wall-openai-ceo-sam-altman-potentially-responds-to-stunted-development-of-advanced-ai-models-reports-due-to-critical-knowledge-cap) [There is no spoon.](https://www.youtube.com/watch?v=XO0pcWxcROI) The scaling will continue. And any perception that scaling has somehow asymptoted is merely a reflection of the limited intelligence of the reader. End of story. (laughs)

**PD**: That’s amazing. That’s fantastic. Should we close on that?

**AWG**: On that note. Wonderful, Peter!

**PD:**Thank you so much Alex, I appreciate that.

**AWG:**Thank you!

**PD:** That’s amazing.
