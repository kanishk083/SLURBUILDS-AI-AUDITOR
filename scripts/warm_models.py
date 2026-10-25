from backend.runtime import embed, score_pairs

print("Loading embedding model...", flush=True)
print("Dimensions:", len(embed(["A reference passage."])[0]), flush=True)
print("Loading NLI verifier...", flush=True)
print(score_pairs([("The sky is blue.", "The sky is blue.")]), flush=True)
