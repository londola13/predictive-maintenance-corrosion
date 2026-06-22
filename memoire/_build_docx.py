# -*- coding: utf-8 -*-
"""Pré-traite memoire_v4.md pour la conversion Word (sauts de page openxml)."""
import re

src = open("memoire_v4.md", encoding="utf-8").read()

pagebreak = (
    "\n```{=openxml}\n"
    '<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n'
    "```\n"
)

# \newpage seul sur sa ligne -> saut de page Word
src, n = re.subn(r"(?m)^\\newpage[ \t]*$", pagebreak, src)

# retirer les commentaires HTML de séparation décoratifs
src = re.sub(r"(?m)^<!--.*-->[ \t]*$", "", src)

open("_memoire_tmp.md", "w", encoding="utf-8").write(src)
print("Sauts de page convertis :", n)
