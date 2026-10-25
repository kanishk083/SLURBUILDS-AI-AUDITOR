# Experiment / decision notebook template

Har experiment ke liye is template ki copy banao. Prediction result dekhne se pehle likho.

## Question

Kaunsa specific behavior samajhna hai?

## Research

- Primary source + section + accessed date:
- Source actually kya establish karta hai?
- Hamara inference kya hai?

## Hypothesis

Mujhe lagta hai ___, kyunki ___. Agar true hua toh ___ observe hoga. Refute tab hoga jab ___.

## Dependencies and blast radius

Target files/modules, upstream inputs, downstream effects aur wrong hone par impact.

## Experiment design

- Corpus version/hash:
- Evaluation set version; development ya held-out:
- Provider/model/version/dimension, if applicable:
- Code revision or source snapshot identifier:
- Main variable:
- Fixed controls, including permissions and filters:
- Commands and environment:
- Repeated trials / warm-cold cache conditions:
- Metric definitions and denominator:
- Expected result, recorded before running:

## Actual observations

| Configuration | Relevant metric | Latency | Resource/cost | Failure examples |
| --- | --- | --- | --- | --- |
| Baseline | Not measured | Not measured | Not measured | Pending |
| Candidate | Not measured | Not measured | Not measured | Pending |

## Understanding check

1. Mechanism apne words mein explain karo.
2. Ek input badalne par expected output predict karo.
3. Ek failure reproduce karo aur cause locate karo.

## Decision

Confirmed / refuted / inconclusive. Kya adopt kar rahe hain, kyun, known limitations aur revisit trigger. Inconclusive evidence ko success mat label karo.

## Durable learning

Kya non-obvious nikla? Kya upfront jaanne se time bachta? Qualifying finding local memory mein save karo, phir Obsidian mirror; secrets aur raw private documents mat copy karo.
