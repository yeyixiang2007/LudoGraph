# 参考文献与来源核验（04）

- **文档集：** `docs/research/game-design-theory/`
- **上位文件：** [`00-framework.md`](./00-framework.md)
- **性质：** 可核验来源清单 + 明确的未核验清单
- **标注：** ✅ 已核验（本次检索直接读到元数据/正文）｜⚠️ 部分核验｜❓ **[unverified]** 未能核验

---

## 0. 如何使用本文

### 0.1 引用纪律

**【本次综合推断】三条规则：**

1. **引用 ✅ 条目**时，使用本文给出的 DOI/URL/ISBN。**不要**用二手转述的引用格式。
2. **引用 ⚠️ 条目**时，必须在正文保留该条目的限定语（如「据摘要」）。
3. **引用 ❓ 条目**时，**必须**在正文标 `[unverified]`，或先补检后再引用。**不得**把 ❓ 当作 ✅ 使用。

### 0.2 本次核验方法与局限

**【事实】方法：** 通过 Crossref（DOI 解析）、出版社官网、期刊官网、作者个人站、机构存档、DiGRA 数字图书馆进行直接抓取核验。

**【事实】主要局限：**

- 本次检索期间多个检索与存档服务**严重限流**（Exa 返回 HTTP 429；Wikipedia 返回 HTTP 403；部分 web.archive.org 快照被限流）。因此**部分条目的核验深度受限**。
- **未**系统检索非英文文献（中文、日文、韩文等）。见 `01` 第 9 节第 2 条。
- **未**核验任何元分析的**具体效应量数值**。见 `01` 第 5.3 节。
- 若干条目在本次核验中**发现来源污染**（见第 5 节），已单独列出。

---

## 1. 游戏学与游戏定义（对应 `01` 第 1 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 1.1 | Huizinga, J. *Homo Ludens: A Study of the Play-Element in Culture*. Routledge. | ✅ | ISBN 9780415487559；<https://www.routledge.com/Homo-Ludens-ILS-86/Huizinga/p/book/9780415487559> |
| 1.2 | Caillois, R. *Man, Play and Games*. University of Illinois Press. | ✅ | <https://www.press.uillinois.edu/books/?id=p070334> |
| 1.3 | Consalvo, M. "There Is No Magic Circle." *Games and Culture* 4(4), 2009. | ✅ | DOI 10.1177/1555412009343575 |
| 1.4 | Henricks, T. "Caillois's *Man, Play, and Games*: An Appreciation and Evaluation." *American Journal of Play* 3(2). | ⚠️ | 期刊与卷期确认；页码未核验 |
| 1.5 | *Games and Culture*（2019）Caillois 细读批评 | ⚠️ | DOI 10.1177/1555412019853080（篇名与页码未核验） |
| 1.6 | Fickle, T. *The Race Card: From Gaming Technologies to Model Minorities*. NYU Press, 2019. | ✅ | 精装 ISBN 9781479868551；<https://nyupress.org/9781479805952/the-race-card/>；出版社页确认不同版本 ISBN、出版日期和章节信息（URL 对应平装 ISBN） |
| 1.7 | Trammell, A. *Repairing Play: A Black Phenomenology*. MIT Press, 2023. | ✅ | 平装 ISBN 9780262545273；<https://mitpress.mit.edu/9780262545273/repairing-play>；MIT Press 书目页确认作者、出版日期和开放获取信息；开放获取版 DOI <https://doi.org/10.7551/mitpress/14656.001.0001> |
| 1.8 | Aarseth, E. *Cybertext: Perspectives on Ergodic Literature*. Johns Hopkins UP, 1997. | ✅ | <https://www.press.jhu.edu/books/title/1398/cybertext> |
| 1.9 | Aarseth, E. "Computer Game Studies, Year One." *Game Studies* 1(1), 2001. | ✅ | <https://www.gamestudies.org/0101/editorial.html> |
| 1.10 | Juul, J. "The Game, the Player, the World: Looking for a Heart of Gameness," 2003. | ✅ | <https://jesperjuul.net/text/gameplayerworld/> |
| 1.11 | Juul, J. *Half-Real: Video Games between Real Rules and Fictional Worlds*. MIT Press, 2005. | ✅ | ISBN 9780262101103；<https://mitpress.mit.edu/9780262101103/half-real/> |
| 1.12 | Zagal, J. P., Mateas, M., Fernández-Vara, C., Hochhalter, B., Lichti, N. "Towards an Ontological Language for Game Analysis." DiGRA 2005. | ✅ | DOI 10.26503/dl.v2005i1.136 |
| 1.13 | GOP（Game Ontology Project）官网 | ⚠️ | <https://gameontology.org/> — **见第 5 节污染警告** |

---

## 2. 规范性设计框架（对应 `01` 第 2 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 2.1 | Church, D. "Formal Abstract Design Tools." *Game Developer*, 1999. | ✅ | <https://www.gamedeveloper.com/design/formal-abstract-design-tools> |
| 2.2 | Hunicke, R., LeBlanc, M., Zubek, R. "MDA: A Formal Approach to Game Design and Game Research." AAAI Workshop, 2004. | ✅ | <https://www.cs.northwestern.edu/~hunicke/MDA.pdf> |
| 2.3 | Kreimeier, B. "The Case for Game Design Patterns." *Gamasutra*, 2002. | ✅ | <https://www.gamedeveloper.com/design/the-case-for-game-design-patterns> |
| 2.4 | Björk, S., Lundgren, S., Holopainen, J. "Game Design Patterns." DiGRA 2003. | ✅ | DOI 10.26503/dl.v2003i1.60 |
| 2.5 | Björk, S., Holopainen, J. *Patterns in Game Design*. Charles River Media, 2005. | ✅ | ISBN 1-58450-354-8；无 DOI |
| 2.6 | Björk & Holopainen, "Gameplay Design Patterns" wiki | ✅ | <https://gdp.cse.chalmers.se/>（旧 <http://virt10.itu.chalmers.se/> 迁移中） |
| 2.7 | Schell, J. *The Art of Game Design: A Book of Lenses*. 3rd ed., 2019. | ✅ | DOI 10.1201/b22101 |
| 2.8 | Schell, J. *The Art of Game Design*. 1st ed., 2008. | ✅ | DOI 10.1201/9780080919171；ISBN 978-1-138-63205-9 |

> **MDA DOI 状态：** 本次未确认 MDA 论文的 DOI。不要把仅凭标题相似检索到的 DOI 当作该文 DOI；引用原始 PDF 或正式会议记录，直到能直接核对对应的 proceedings 元数据。

---

## 3. 机制、时间性、能动性（对应 `01` 第 3 节与 4.6 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 3.1 | Sicart, M. "Defining Game Mechanics." *Game Studies* 8(2), 2008. | ✅ | <https://gamestudies.org/0802/articles/sicart> |
| 3.2 | Wardrip-Fruin, N. *Expressive Processing: Digital Fictions, Computer Games, and Software Studies*. MIT Press, 2009. | ✅ | ISBN 9780262013437；<https://mitpress.mit.edu/9780262013437/expressive-processing/> |
| 3.3 | Zagal, J. P., Mateas, M. "A Unifying Framework for the Analysis of Game Temporality." DiGRA 2007. | ✅ | <https://users.soe.ucsc.edu/~michaelm/publications/zagal-digra2007.pdf> |
| 3.4 | Zagal, J. P., Fernández-Vara, C., Mateas, M. "Rounds, Levels, and Waves: The Early Evolution of Gameplay Segmentation." | ⚠️ | 篇名与作者确认；期刊/年份未核验 |
| 3.5 | Mitchell, A., Khosla, M., Jaimes, A., and others. *Towards an Agency-centered Ontology of Game Mechanics*. ACM, 2023. | ✅ | DOI 10.1145/3582437.3587201；ACM DOI 落地页及论文来源 |
| 3.6 | Murray, J. *Hamlet on the Holodeck*. MIT Press, 1997. | ✅ | <https://mitpress.mit.edu/9780262533485/hamlet-on-the-holodeck/> |
| 3.7 | **对 agency 的规范批评文献** | ❓ | **[unverified]** 未定位到单一权威出处 — 见第 6 节 |

---

## 4. 意义、程序修辞、批评理论（对应 `01` 第 4 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 4.1 | Bogost, I. *Persuasive Games: The Expressive Power of Videogames*. MIT Press, 2007. | ✅ | DOI 10.7551/mitpress/5334.001.0001；ISBN 9780262026147；<https://mitpress.mit.edu/9780262026147/persuasive-games/> |
| 4.2 | Bogost, I. "The Rhetoric of Video Games." In *The Ecology of Games* (Salen, ed.), MIT Press, 2008. | ✅ | <https://www.se4n.org/papers/bogost-rhetoric.pdf> |
| 4.3 | Bogost, I. *Play Anything: The Pleasure of Limits, the Uses of Boredom, and the Secret of Games*. Basic Books, 2016. | ✅ | ISBN 9780465051724；<http://bogost.com/books/play-anything/> |
| 4.4 | Sicart, M. "Against Procedurality." *Game Studies* 11(3), 2011. | ✅ | <https://gamestudies.org/1103/articles/sicart_ap> |
| 4.5 | Anderson, B. R., Karzmark, C. R., Wardrip-Fruin, N. "The Psychological Reality of Procedural Rhetoric." FDG 2019. | ✅ | DOI 10.1145/3337722.3337751；<https://barrettrees.com/papers/Anderson%20Karzmark%20Wardrip-Fruin%202019%20The%20Psychological%20Reality%20of%20Procedural%20Rhetoric.pdf>（全文已读） |
| 4.6 | Ferrara, J. "Games for Persuasion: Argumentation, Procedurality, and the Lie of Gamification." *Games and Culture* 8(4), 2013. | ✅ | DOI 10.1177/1555412013496891 |
| 4.7 | Seiffert, J., Nothhaft, H. "The missing media: The procedural rhetoric of computer games." *Public Relations Review* 41(2), 2015. | ✅ | DOI 10.1016/j.pubrev.2014.11.011 |
| 4.8 | Sicart, M. *The Ethics of Computer Games*. MIT Press, 2009. | ✅ | <https://direct.mit.edu/books/monograph/2301/> |
| 4.9 | Sicart, M. *Beyond Choices: The Design of Ethical Gameplay*. MIT Press, 2013. | ✅ | ISBN 9780262019781；<https://mitpress.mit.edu/9780262538794/beyond-choices/> |
| 4.10 | Sicart, M. *Play Matters*. MIT Press（Playful Thinking 系列）, 2014. | ✅ | ISBN 9780262027366；<https://direct.mit.edu/books/book/4467/Play-Matters>（二印 2017, ISBN 9780262534512） |
| 4.11 | Deterding, S. "A Manifesto, With Footnotes"（评 *Play Matters*）. *Game Studies* 15(1). | ✅ | <https://gamestudies.org/1501/articles/deterding_s> |
| 4.12 | Flanagan, M. *Critical Play: Radical Game Design*. MIT Press, 2009. | ✅ | ISBN 9780262062688 / 9780262518659；<https://direct.mit.edu/books/monograph/2338/> |
| 4.13 | Galloway, A. R. *Gaming: Essays on Algorithmic Culture*. U Minnesota Press, 2006. | ✅ | ISBN 9780816648511；JSTOR 10.5749/j.ctttss5p |
| 4.14 | Dyer-Witheford, N., de Peuter, G. *Games of Empire: Global Capitalism and Video Games*. U Minnesota Press, 2009. | ✅ | ISBN 9780816666119；<https://www.upress.umn.edu/9780816666119/games-of-empire/> |
| 4.15 | Ruberg, B., Shaw, A. (eds.) *Queer Game Studies*. U Minnesota Press, 2017. | ✅ | ISBN 9781517900373；<https://www.upress.umn.edu/9781517900373/queer-game-studies/> |
| 4.16 | Ford, D. "『eXplore, eXpand, eXploit, eXterminate』: Affective Writing of Postcolonial History and Education in *Civilization V*." *Game Studies* 16(2). | ✅ | <https://www.gamestudies.org/1602/articles/ford> |
| 4.17 | Widlok, "Decolonizing Gaming." Springer 章节（年份显示为 2025） | ⚠️ | DOI 10.1007/978-3-032-11043-5_23；<https://link.springer.com/chapter/10.1007/978-3-032-11043-5_23>（作者全名与年份未核验） |

### 4.5 ludology vs narratology（对应 `01` 第 4.5 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 4.17 | Frasca, G. "Ludologists Love Stories, Too: Notes from a Debate that Never Took Place." Level Up / DiGRA 2003. | ✅ | <https://dl.digra.org/index.php/dl/article/view/64> |
| 4.18 | Aarseth, E. "A Narrative Theory of Games." FDG 2012. | ✅ | DOI 10.1145/2282338.2282365 |
| 4.19 | Murray, J. "The Last Word on Ludology v Narratology in Game Studies," 2005. | ✅ | 作者站可核验 |
| 4.20 | Ryan, M.-L. *Avatars of Story*. U Minnesota Press, 2006（第 8 章）. | ✅ | DOI 10.25969/mediarep/17696 |
| 4.21 | Jenkins, H. "Game Design as Narrative Architecture," 2004. | ✅ | <https://web.mit.edu/~21fms/People/henry3/games%26narrative.html> |
| 4.22 | Aarseth, E. "Genre Trouble: Narrativism and the Art of Simulation," 2004. | ✅ | <https://electronicbookreview.com/publications/genre-trouble/> |
| 4.23 | Vossen, H. "Young Scholars, and Old Debates: Why the Ludology Versus Narratology 'Debate' Cannot Be Forgotten." In *Historiographies of Game Studies*, punctum books, 2025. | ✅ | DOI 10.53288/0441.1.04 |

---

## 5. 玩家体验实证研究（对应 `01` 第 5 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 5.1 | Csikszentmihalyi, M. *Flow: The Psychology of Optimal Experience*. Harper & Row, 1990. | ✅ | 无 DOI；书目形态经 Ryan/Rigby/Przybylski 2006 参考文献核实 |
| 5.2 | Ryan, R. M., Rigby, C. S., Przybylski, A. "The motivational pull of video games: A self-determination theory approach." *Motivation and Emotion* 30(4): 344–360, 2006. | ✅ | DOI 10.1007/s11031-006-9051-8 |
| 5.3 | Lazzaro, N. "Why We Play: Affect and the Fun of Games." | ✅ | 2007: DOI 10.1201/9781410615862.ch34；2009: DOI 10.1201/9781420088885.ch10；2012: DOI 10.1201/b11963-36 |
| 5.4 | Michailidis, L., Balaguer-Ballester, E., He, X. "Flow and Immersion in Video Games: The Aftermath of a Conceptual Challenge." *Frontiers in Psychology* 9:1682, 2018. | ✅ | DOI 10.3389/fpsyg.2018.01682 |
| 5.5 | Jagoda, P. *Against Flow: Video Games and the Flowing Subject*. MIT Press, 2021. | ✅ | DOI 10.7551/mitpress/12831.003.0005（章节级） |
| 5.6 | "Player Enjoyment in Video Games: A Systematic Review and Meta-analysis of the Effects of Game Design Choices." *Int. J. Human–Computer Interaction* 40(16). | ⚠️ | DOI 10.1080/10447318.2023.2210880；**全文未读取，效应量未核验** |
| 5.7 | "Effects of game design choices on player experience: a synthesis of four meta-analyses on presence, immersion, enjoyment and flow"（四元分析综述） | ❓ | **[unverified]** 仅见聚合库链接，未能打开全文；作者/期刊/年份未核验 |
| 5.8 | Lazzaro, "Four Keys to Fun"（*Gamasutra* 文章） | ❓ | **[unverified]** 无稳定在线链接（存档限流/404）。**改引条目 5.3。** |

---

## 6. 机器可处理的领域表示与通用形式化工具（对应 `01` 第 6 节）
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 6.1 | GDL 官方说明（Stanford GGP） | ✅ | <http://ggp.stanford.edu/overview/game_description.html> |
| 6.2 | GDL-III（不完全信息/认知游戏扩展）, IJCAI 2017 | ✅ | <https://www.ijcai.org/proceedings/2017/177> |
| 6.3 | Berlekamp, E., Conway, J. H., Guy, R. *Winning Ways for Your Mathematical Plays*. Academic Press, 2 vols., 1982（2nd ed. A K Peters, 4 vols., 2001–2004）. | ✅ | 1st ed. ISBN 0-12-091150-7 / 0-12-091152-3；<https://math.berkeley.edu/~berlek/pubs/books.html> |
| 6.4 | von Neumann, J., Morgenstern, O. *Theory of Games and Economic Behavior*. Princeton UP, 1944（60th-anniversary ed. 2004）. | ✅ | ISBN 9780691130613；<https://press.princeton.edu/books/paperback/9780691130613/theory-of-games-and-economic-behavior> |
| 6.5 | 对**经济博弈论**作为解释性社会科学的批评（非 CGT×体验） | ✅ | Grüne-Yanoff, "Reducible and Nonsensical Uses of Game Theory," *Philosophy of the Social Sciences*，DOI 10.1177/0048393108315557；Syll, *real-world economics review* 83，<https://www.paecon.net/PAEReview/issue83/Syll83.pdf> |
| 6.6 | 论证「CGT 无法刻画被设计的玩家体验」的**专门**文献 | ❓ | **[unverified]** 本次未找到（见第 7 节） |
| 6.7 | 论证「Kreimeier / FADT 有正式发表批评」的文献 | ❓ | **[unverified]** 本次未找到 |

> **【本次综合推断】条目 6.6 与 6.7 的缺席要在正文中保留为缺口。** 「没有找到批评」**不等于**「没有批评」。`01` 第 6.2 节与第 2.2 节已按此处理。
>
> **【本次综合推断】注意 6.5 的性质：** 已核验的三条文献批评的是**经济博弈论作为社会科学解释框架**的效力（实验对象不采用预测中的策略/均衡），而**不是**「CGT 无法刻画被设计的体验」。二者是**不同**的论点。**不要**把它们当作 `01` 第 6.2 节那一论断的证据——那一论断仍是【本次综合推断】。

---

## 7. 案例来源（对应 `02`）

### 7.1 国际象棋
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.1.1 | *FIDE Laws of Chess*（2023-01-01 生效） | ✅ | <https://handbook.fide.com/chapter/e012023> |
| 7.1.2 | threefold repetition 说明 | ✅ | <https://www.chess.com/terms/threefold-repetition-chess> |
| 7.1.3 | Endgame Tablebases | ✅ | <https://www.chessprogramming.org/Endgame_Tablebases> |
| 7.1.4 | **「七子残局已解出」的具体子数** | ❓ | **[unverified]** 不得引用具体子数 |

### 7.2 Monopoly / The Landlord's Game
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.2.1 | "The secret history of Monopoly." *The Guardian*, 2015-04-11. | ✅ | <https://www.theguardian.com/lifeandstyle/2015/apr/11/secret-history-monopoly-capitalist-game-leftwing-origins> |
| 7.2.2 | **Magie「反垄断教学装置」逐字引语** | ❓ | **[unverified]** 主旨有报道支持，精确引语未核验 |
| 7.2.3 | Smithsonian 关于 Magie 的相关说法 | ❓ | **[unverified]** 仅来自搜索摘要 |

### 7.3 Space Invaders
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.3.1 | Nishikado 访谈, One Million Power | ✅ | <https://www.onemillionpower.com/once-again-asking-the-father-of-space-invaders-about-its-creation/> |
| 7.3.2 | Space Invaders 硬件分析, Computer Archaeology | ✅ | <http://computerarcheology.com/Arcade/SpaceInvaders/Hardware.html> |
| 7.3.3 | **「加速源于硬件限制」的一手归因** | ❓ | **[unverified]** 未找到 Nishikado 本人的归因引语 |
| 7.3.4 | 「排头兵逐帧移动」的机制解释 | ❓ | **[unverified]** 来源为复古计算社区（二级）；机制现象本身为【事实】 |

### 7.4 Pac-Man
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.4.1 | Pittman, J. "The Pac-Man Dossier." | ✅ | <https://www.gamedeveloper.com/design/the-pac-man-dossier> |
| 7.4.2 | **「Pac-Man 被设计为吸引女性玩家/非暴力」的一手引语** | ❓ | **[unverified]** Time/Gamasutra 原始访谈未定位 |
| 7.4.3 | 逐元素「1-1 式」教学分析 | — | 见 7.10 |

### 7.5 文明系列
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.5.1 | Meier, "The Psychology of Game Design (Everything You Know Is Wrong)." GDC Vault 摘要 | ✅ | <https://www.gdcvault.com/play/1012186/The-Psychology-of-Game-Design> |
| 7.5.2 | "Just one more turn..." *Game Developer* | ✅ | <https://www.gamedeveloper.com/design/just-one-more-turn---game-development-tips-and-tricks-from-the-creator-of-civilization-sid-meier-> |
| 7.5.3 | **Meier 本人口述「one more turn」的视频逐字** | ❓ | **[unverified]** 须补检 GDC 视频 |
| 7.5.4 | Ford, D. *Game Studies* 16(2)（见 4.16） | ✅ | <https://www.gamestudies.org/1602/articles/ford> |

### 7.6 The Sims
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.6.1 | "Making Of: The Sims." *Rock Paper Shotgun* | ✅ | <https://www.rockpapershotgun.com/making-of-the-sims> |
| 7.6.2 | 1994 *Wired* 的 "Dollhouse" 最早引语 | ❓ | **[unverified]** 仅由 GameSpot 存档摘要支持 |

### 7.7 Magic: The Gathering
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.7.1 | *Magic Comprehensive Rules* | ✅ | <https://magic.wizards.com/en/rules> |
| 7.7.2 | Rosewater, "Mechanical Color Pie 2021" | ✅ | <https://magic.wizards.com/en/news/making-magic/mechanical-color-pie-2021> |
| 7.7.3 | Garfield, "The Creation of Magic: The Gathering"；「metagame」词源 | ❓ | **[unverified]** 原文未抓取 |
| 7.7.4 | 「color pie」的官方定义性引语 | ❓ | **[unverified]** 2021 文中的定义句未核验 |

### 7.8 Battle Pass / 服务型游戏
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.8.1 | "Battle pass capitalism." *Sage*（期刊名待确认） | ⚠️ | DOI 10.1177/1469540521993930；**作者/年份/卷期未核验** |
| 7.8.2 | DiVA 学位论文（battle pass × dark patterns） | ❓ | **[unverified]** 作者/标题/年份未核验 |
| 7.8.3 | Zanescu et al. GREO 2020 报告 | ⚠️ | <https://www.greo.ca/>；仅摘要级 |
| 7.8.4 | **服务型游戏的一手设计意图陈述** | ❓ | **[unverified]** 未获得 |

### 7.9 放置/增量游戏
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.9.1 | Alharthi et al. "Playing to Wait: A Taxonomy of Idle Games." CHI 2018 | ⚠️ | 篇名确认；作者列表与 DOI **未核验** |
| 7.9.2 | Wikipedia "Incremental game" | ⚠️ | 仅摘要级 |
| 7.9.3 | **一手设计意图陈述** | ❓ | **[unverified]** 未获得 |

### 7.10 超级马里奥兄弟 World 1-1
| # | 条目 | 状态 | 标识 |
| --- | --- | --- | --- |
| 7.10.1 | IGN 转述 Miyamoto 访谈（1-1 是「学校」） | ⚠️ | <https://www.ign.com/articles/miyamoto-explains-how-super-mario-bros-world-1-1-was-created>；**二手转述** |
| 7.10.2 | **Eurogamer 原始访谈 URL** | ❓ | **[unverified]** 未定位 |
| 7.10.3 | 逐元素「哪个砖块教什么」的教学分析 | ❓ | **[unverified]** 无一手设计文档支持；应视为社区解读 |

---

## 8. 来源污染与来源可靠性事故（重要）

**【事实】本次检索中直接遇到三起来源可靠性问题。这不是附注，而是本文档集可信度结构的一部分。**
| # | 来源 | 问题 | 处理 |
| --- | --- | --- | --- |
| 8.1 | <https://gameontology.org/> | 首页被与主题无关的**商业推广内容**（在线交易平台）注入 | 实质内容仍可复核；已在 `01` 第 1.3 节与 `02` 中标注为**来源可靠性警告** |
| 8.2 | `boardgamestudies.info` | 域名现已指向**无关垃圾站** | 不作为来源 |
| 8.3 | 多个 web.archive.org 快照 | 被限流，无法核验 | 相关条目降级为 ⚠️ 或 ❓ |

**【本次综合推断】8.1 与 LudoGraph 的直接关系：** LudoGraph 的核心主张之一是**证据可追溯**。本次研究提供的实证是：**「域名正确」不等于「内容可信」**，即便是一手来源的域名也可能被注入或劫持。因此抽取管线在 S1（来源登记）阶段需要**页面内容与主题一致性检查**，而不能只依赖域名白名单。见 `03` 第 1 节 S1 第 3 点。

---

## 9. 未核验项完整清单（引用前必须处理）

**【事实】以下 20 项本次**未能核验**。任何一处被引用时，正文**必须**保留 `[unverified]`，或先补检。**
| # | 未核验项 | 出现在 |
| --- | --- | --- |
| 1 | 「agency gap」的单一权威批评文献出处 | `01` §4.6 |
| 2 | Bogost 是否**正式撤回**程序修辞（一手来源） | `01` §4.2 |
| 3 | DiGRA「Playgrounds of Whiteness」论文的作者与年份 | `01` §4.4 |
| 4 | Rizvi/Mukherjee 2023 的确切标题与出处 | `01` §4.4 |
| 5 | Grace 2023 的确切标题与出处 | `01` §4.4 |
| 6 | 元分析的**具体效应量数值** | `01` §5.3 |
| 7 | Miyamoto 访谈的 Eurogamer 一手 URL | `01` §7.2；`02` 案例 10 |
| 8 | Lazzaro "Four Keys to Fun" 的稳定在线链接 | `01` §5.1 |
| 9 | 国际象棋「七子残局已解出」的具体子数 | `02` 案例 1 |
| 10 | Magie「反垄断教学装置」的逐字引语 | `02` 案例 2 |
| 11 | Smithsonian 关于 Magie 的说法 | `02` 案例 2 |
| 12 | Nishikado 把加速**归因于**硬件限制的引语 | `02` 案例 3 |
| 13 | Space Invaders「排头兵逐帧移动」的一手机制解释 | `02` 案例 3 |
| 14 | Pac-Man「吸引女性玩家/非暴力」的一手引语 | `02` 案例 4 |
| 15 | Meier 本人口述「one more turn」的视频逐字 | `02` 案例 5 |
| 16 | *Wired* 1994 "Dollhouse" 最早引语 | `02` 案例 6 |
| 17 | Garfield "The Creation of Magic: The Gathering" 原文 | `02` 案例 7 |
| 18 | battle pass 各条目的作者/年份/卷期（7.8.1–7.8.3） | `02` 案例 8 |
| 19 | Alharthi et al. CHI 2018 的作者列表与 DOI | `02` 案例 9 |
| 20 | Mario 1-1 逐元素教学分析的一手来源 | `02` 案例 10 |

**【本次综合推断】这份清单的用途：** 它不是「已知缺陷列表」，而是**下一步工作的输入**。清单中的第 1、2、3、4、5、7、9、10、12、14、15、19 项都是**可以通过一次定向检索或抓取解决的**；第 6 项需要获取元分析全文；第 18 项需要访问 DOI 落地页。

---

## 10. 检索方法说明

**【事实】本次研究采用的检索路径：**

1. **DOI 解析：** 通过 Crossref API / DOI 落地页确认作者、年份、卷期、页码。
2. **出版社与期刊官网：** MIT Press、U Minnesota Press、Routledge、Illinois UP、Johns Hopkins UP、NYU Press、Sage、Frontiers、ACM Digital Library。
3. **开放期刊与机构存档：** *Game Studies*、*American Journal of Play*、DiGRA 数字图书馆、eScholarship/UCSC、MIT 开放课程页面、punctum books（开放获取）。
4. **一手设计者材料：** GDC Vault、*Game Developer*/*Gamasutra* 存档文章、Rock Paper Shotgun、开发方官方规则文档。
5. **作者个人站：** 如 <https://jesperjuul.net/>。
6. **社区/众包来源：** 仅用于**机制现象**的旁证，且**全部**降级标注（见 7.3.4、7.10.3）。

**【事实】检索的已知失败模式：**

- **限流：** Exa（HTTP 429）、Wikipedia（HTTP 403）、部分 web.archive.org 快照。
- **页面被污染：** 见第 8 节。
- **无稳定在线版本：** 部分 2000 年代初的网站文章（如 Lazzaro 的 *Gamasutra* 文章）已无可用在线存档。

**【本次综合推断】给后续工作的建议：**

1. **优先解决第 9 节清单中「可通过定向检索解决」的条目**，它们能显著提升本文档集的可核验比例。
2. **补充非英文文献检索**（见 `01` 第 9 节第 2 条），这是本文件集最大的系统性偏差。
3. **不要**通过降低标注标准的方式来「解决」未核验项。留空比填错更有价值。

---

**返回：** [`00-framework.md`](./00-framework.md)｜[`01-theory-landscape.md`](./01-theory-landscape.md)｜[`02-classic-cases.md`](./02-classic-cases.md)｜[`03-analysis-method.md`](./03-analysis-method.md)
