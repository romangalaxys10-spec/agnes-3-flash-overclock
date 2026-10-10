When producing Russian short-video scripts, source-preserving rewrites, or constrained JSON with Agnes 3.0 Flash (agnes-3.0-flash):
1. Generate with the tested v1 generation prompt, then run the v1 editor pass (prompts/v1-generation-tested.txt, prompts/v1-editor-tested.txt).
2. Validate the final payload with the offline checker (check.py, or the agnes_check MCP tool). Never trust the model to count its own words.
3. Do not add heavy planning prompts on their own: in the small benchmark they scored worse (71%) than the plain task (84%). Adapted prompt + editor scored 88% (n=2 per cell, directional).
4. The code-validated v2 repair loop is UNTESTED against Agnes. Always review facts and voice manually; the checker cannot catch invented facts.
