# Technocore Lobby Activity Analysis

A small reproducible analysis of message activity in the Technocore lobby.

## Research Question

How much identity diversity and message-text diversity appear in short Technocore lobby activity windows?

The goal was to compare unique DIDs with exact message repetition, without assuming that a unique DID represents a unique human or operator.

## Dataset

Three separate snapshots of the Technocore `lobby` room were collected.

Each snapshot contains 200 messages.

Total observations:

* 600 messages
* 3 snapshots
* 200 messages per snapshot

Each message contains:

* `seq`
* `ts`
* `from`
* `text`
* `nonce`

The raw JSON snapshots are available in the `data/` directory.

## Method

The analysis compares:

* Total messages
* Unique DIDs
* DIDs appearing more than once
* Unique exact message texts
* Messages belonging to repeated exact-text groups
* Repeated-text rate
* Exact message templates appearing across all three snapshots
* Concentration of persistent templates

The analysis can be reproduced by running:

```bash
python analysis/analyze.py
```

## Results

Across 600 messages:

* 589 unique DIDs
* 98.2% DID uniqueness
* 10 DIDs appeared more than once
* Maximum appearances by one DID: 3
* 188 unique exact message texts
* 431 messages belonged to repeated exact-text groups
* Combined repeated-text rate: 71.8%
* 15 exact message templates appeared in all three snapshots
* Those 15 persistent templates accounted for 422 of 600 messages
* Persistent-template share: 70.3%

The main observation is the contrast between identity diversity and content diversity.

The sampled activity showed very high DID diversity while a large share of messages belonged to recurring exact-text templates.

## Interpretation

These results do not prove that repeated-message DIDs are controlled by the same person, that they are Sybil identities, or that every repeated message is automated.

A DID represents a cryptographic identity. It does not establish a unique human or operator.

The analysis only shows that, in these three sampled windows, high DID diversity coexisted with substantial exact-text repetition.

## Limitations

This is a small observational dataset.

The analysis covers only:

* 600 messages
* Three short sampling windows
* The Technocore `lobby` room
* Exact-text matching only

It does not capture semantic similarity between differently worded messages, long-term DID behavior, operator identity, or activity across the wider Technocore network.

The results should therefore be treated as findings about these sampled windows, not as a characterization of all Technocore activity.

## Repository Structure

```text
technocore-lobby-analysis/
├── README.md
├── .gitignore
├── analysis/
│   └── analyze.py
└── data/
    ├── lobby_200.json
    ├── lobby_200_2.json
    └── lobby_200_3.json
```
