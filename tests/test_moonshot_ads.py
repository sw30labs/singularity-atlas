"""Framed mid-roll detection — Blitzy VO, Fountain host-reads, resume cues."""

from __future__ import annotations

from singularity_atlas.moonshot_ads import content_text, spans, tag_segments


def _seg(text, start, speaker="Peter Diamandis"):
    return {"text": text, "start": start, "speaker": speaker}


class TestTagSegments:
    def test_blitzy_unknown_speaker_is_ad(self):
        segs = [
            _seg("Welcome back.", 0),
            _seg("I think AGI will be here by 2027.", 8, "Mo Gawdat"),
            _seg("This episode is brought to you by Blitzy, autonomous software "
                 "development with infinite code context. Visit blitzy.com.",
                 20, ""),
            _seg("OpenAI is not the only lab.", 90, "Mo Gawdat"),
        ]
        tagged = tag_segments(segs)
        assert tagged[1]["is_ad"] is False
        assert tagged[2]["is_ad"] is True
        assert tagged[2]["ad_brand"] == "blitzy"
        assert tagged[3]["is_ad"] is False
        body = content_text(tagged).lower()
        assert "blitzy" not in body
        assert "agi will be here" in body

    def test_fountain_host_read_with_closer(self):
        segs = [
            _seg("Next topic is robots.", 0, "Dave Blundin"),
            _seg("I want to take a short break from our episode. "
                 "The company is called Fountain Life. "
                 "Go to fountainlife.com slash Peter. "
                 "All right, let's go back to the episode.", 40),
            _seg("Anyway, the gigawatt campus.", 120, "Dave Blundin"),
        ]
        tagged = tag_segments(segs)
        assert tagged[0]["is_ad"] is False
        assert tagged[1]["is_ad"] is True
        assert tagged[1]["ad_brand"] == "fountain_life"
        assert tagged[2]["is_ad"] is False
        assert spans(tagged)

    def test_guest_company_chat_is_not_an_ad(self):
        segs = [
            _seg("Naveen, you built Viome as a diagnostics company.", 0),
            _seg("We sequence the gut microbiome.", 10, "Naveen Jain"),
        ]
        tagged = tag_segments(segs)
        assert not any(s["is_ad"] for s in tagged)
