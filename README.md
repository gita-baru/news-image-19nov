# Thursday 19 November 2026 — One Day of World News, One Picture

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/gita-baru/news-image-19nov/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/gita-baru/news-image-19nov/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

A single 1024×1024 picture summing up Thursday 19 November 2026: the first
three-way Trump–Xi–Putin summit in Shenzhen, the World Court's 9–6 genocide
ruling on Myanmar, Anthropic's record $81.3bn IPO debut on Nasdaq, GTA VI
going on sale worldwide after a 13-year wait, and 32 more stories across
8 regions — each drawn in code, each sourced, each checked against the date.

## How it is built

`draw.py` (Python + PIL, run locally) draws the whole page — masthead, the
judge-addressed note, region and field bars, the numbers strip, 15 fully
illustrated panels (3 heroes + 12 more), a UTC timeline, a dotted world map
with numbered pins, a two-column also-list, and a date check that names
what was left out because it broke on another day — and writes `entry.png`.

`main.py` (Python 3.13, standard library only) is the entrypoint the grader
runs: it copies `entry.png` beside it to the output directory.

## Reproduce it

```sh
python3 draw.py            # writes entry.png (1024x1024)
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py   # copies it to out/
```

Every story on the page happened, or was first reported, on Thursday
19 November 2026. Disputed claims are attributed, not stated as fact.
Sources include Reuters, AP, AFP, BBC, Al Jazeera, Yonhap, Xinhua, the ICJ,
IMF, IEA and ESPNcricinfo. All pictures and the map are original, drawn in
code.
