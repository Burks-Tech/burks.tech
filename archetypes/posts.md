---
title: "{{ replace .File.ContentBaseName "-" " " | strings.FirstUpper }}"
subtitle: ""
date: {{ .Date }}
draft: true
summary: ""
tags: []
toc: false
# Uncomment for a post that summarises a repository:
# source:
#   url: "https://github.com/Burks-Tech/<repo>"
#   rev: "v1.0.0"
#   title: "<repo>"
#   summary: "One sentence on what the repository holds."
# stats:
#   - { value: "", label: "" }
---
