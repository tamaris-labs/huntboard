# Settings

*Version française : [parametrage.md](../fr/parametrage.md)*

On first launch, a **setup assistant** guides the configuration: language and country, CV
import (PDF, Word or text), CV analysis by the AI, which proposes a profile and criteria,
criteria review, then recommended sources for the country. Everything can then be changed in
the **Settings** tab, organised in four groups: Profile and CV, Documents, Search (criteria,
extra tracks, sources) and Learning and data.

<p>
<img src="../screenshots/en/settings-mobile.png" width="200" alt="Completeness">
<img src="../screenshots/en/tuto-12-tracks.png" width="200" alt="Tracks">
<img src="../screenshots/en/tuto-11-documents.png" width="200" alt="Documents">
<img src="../screenshots/en/tuto-14-learning.png" width="200" alt="Learning">
</p>

Step by step: [tutorial.md](tutorial.md).

| Section | Content |
|---|---|
| Profile and CV | CV import and text, analysis with proposals to apply, profile used by the AI, CV translation into seven languages (copy or download) |
| Documents and letters | Original files kept and downloadable (CV as PDF, translated CVs, cover letters); writing a cover letter from a followed posting or a pasted text, the CV and the profile, in seven languages and three lengths, inspired by the letters already saved; editable text, then saved, copied or downloaded |
| Extra tracks | Searches separate from the main feed (freelance assignments, international roles and international organisations, custom track): criteria, expected pay (a day rate for example), sources, daily or weekly frequency, cap per run; by default they stay in a dedicated filter, with no notification and no effect on learning |
| Criteria | Salary floor, archiving, home address (private, can be placed on the map), home and commute and remote-work rules, roles, fields, contracts, exclusions, weighting, co-founder search, free instructions; "Fill with AI from the CV" button |
| Sources | One-click addition of the recommended sources for a country, activation, custom sources with a reading instruction, yield of each source (offers found and followed), **AI source suggestions** and web check (see below) |
| Learning | Trends drawn from your choices, with their effect and justification; each can be revoked |
| Learning and data | Language of the interface and generated texts, main country, connections (self-hosted app), JSON export and import, reset, restart of the setup assistant |

AI suggestions (CV analysis, Assistant tab, "Fill with AI") are never applied on their own:
they are shown field by field, to tick and then apply.

## Tips

- **Triage**: use *Interested* and *Discard* with the reason ticked; after a dozen choices, the
  Learning section fills up and scoring becomes sharper.
- **Sources**: each source's instruction guides the watch ("direct reading refused, use web
  search", "filter by region with ?locations=…"). Page addresses cited in the instruction (for
  example a "CTO jobs in Paris" list page) are also read, including by the self-hosted app
  without web search. See [sources.md](sources.md) for the list by
  country.
- **E-mail alerts**: create precise alerts (title + location or remote) on LinkedIn, Indeed,
  HelloWork; they are read by e-mail, without ever accessing your accounts.
- **Follow-up**: set the next action and its due date on the offer page; the board lists them
  under "To do".

## Source suggestions

In Search › Sources:

1. **Suggest sources with AI**: the AI receives the CV, the criteria, the area and the yield of
   each active source, then proposes up to eight new sources (specialised sites, regional
   networks and clusters, recruitment agencies, careers pages, public programmes, co-founder
   matching services), each with a "why it fits you" sentence and its destination (main search
   or track). It also flags **low-yield sources**, which can be turned off with a tick.
2. **Check and extend on the web**: tests the proposed addresses (checked, address updated,
   closed to robots, unreachable) and looks for a few more sources.
3. Tick the sources to keep, then **Add selection**; *Dismiss* removes a proposal.
4. **Every Monday**, the watch proposes one or two new, checked sources, which join the same
   list and are mentioned in the notification.

Nothing is added or turned off without your choice. The behaviour differs by distribution:

| | Claude kit | Self-hosted app |
|---|---|---|
| AI suggestions | The account's Claude usage, from the model's knowledge: the page has no web access (isolated environment), so addresses are marked "to check" | Configured AI engine; the web button's suggestions rely on the configured web search ([ai-engines.md](ai-engines.md)) |
| Web check | Scheduled task "Huntboard – sources", with no schedule, fired by the button through the "Claude Code Remote" connector; results in a few minutes, with a notification. Enable it once by asking Claude "Enable source checking for my Huntboard"; the first click asks to allow the connector for the page | The app server: page reading and web search (built into the provider, or Brave, Tavily, SearXNG), result in a few seconds |
| Monday proposal | Step 10 ter of the watch task | Built into the Monday run |

## Board

- **This week's momentum**: adjustable weekly goals (applications, offers triaged, network
  contacts with a "+1 contact" button), streak of active days, factual message suited to the
  situation (interview coming up, goal reached, recent rejection), clickable "next small step"
  and progress log (interviews obtained recorded automatically, progress entered by hand). A
  one-line reminder sits at the top of the Offers tab.
- **Map**: two views. The *Map* view shows a real basemap (countries, coastlines, departments)
  with finger panning, pinch and zoom buttons, "Around home", "France" and "World" presets,
  and a button to place your home precisely. The *Radar* view is centred on home, with
  straight-line distances (rings from 10 to 200 km), colour by stage (interview or offer,
  applied, to explore, new); a dot opens the list of offers at that place; upcoming interviews
  are listed alongside.

## Offer page

- **Contacts**: name, role, e-mail and phone of the people involved (direct links to write or
  call); the watch adds those it finds in e-mails and postings.
- **Posting text**: kept in full as soon as the offer is marked "To explore", even if the
  posting later disappears; it can also be pasted by hand. It feeds interview preparation and
  the cover letter.
- **Writing**: the same letter generator (language, length, inspiration from your saved
  letters) as in Documents, plus follow-up, thank-you and LinkedIn messages; editable text,
  copied, downloaded or saved to your documents.
- **Listen**: reads aloud the daily brief, the interview brief, the debrief, the assistant's
  answers and the posting text, with the phone's voice.

## Notifications

Each watch run sends a notification: the news or, on days with nothing new, a short factual
encouragement in your language, based on your open applications and your weekly goals.
