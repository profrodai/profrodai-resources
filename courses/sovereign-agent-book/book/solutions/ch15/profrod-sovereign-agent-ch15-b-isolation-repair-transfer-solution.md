---
jupyter:
  authors:
  - name: Prof Rod
    website: https://profrod.ai
  course:
    book_url: https://profrod.ai/book
    community_url: https://profrod.ai/community
    distribution_version: '2026-09-10'
    edition: nineteen-chapter-v1
    instructor: true
    lesson_id: isolation
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch15-b-isolation-repair-transfer-solution
    self_contained_runtime: true
    source_basis: 444c5f6
    source_unit: ch12-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch15-b
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  language_info:
    name: python
    version: '3.12'
---

<!-- #region -->
# Chapter 15, Unit B: Break, repair and transfer tool isolation

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-09**

This is one of two practical units for Chapter 15. Unit A constructs and connects the
mechanism; Unit B investigates a controlled failure, repairs it and transfers the invariant.
Each is a complete ninety-minute session, with its own setup and required conceptual introductions.
Basic Python variables, conditions, loops, functions, lists and dictionaries are the starting
knowledge. Libraries and specialized concepts used here are introduced below before the main task.

By the end you should be able to:

1. Explain the chapter's mechanism using a prediction and an observed intermediate result.
2. Repair the failure: A known tool can still be unavailable to this particular worker. Install the method in the real Dispatcher and observe handler invocation counters, not just returned text.
3. Solve **separate registration, permission and consequential authority** using changed inputs and an independent expectation.
4. Retain your implementation, failed/corrected observations, causal explanation and limits.

| Minutes | Dedicated activity | Evidence you produce |
|---|---|---|
| 0–5 | State the problem and make a prediction | Initial prediction in your own words |
| 5–25 | Foundations and library examples | Values, explanations, revised predictions |
| 25–35 | Trace setup and the main interface | Input → learner function → observation |
| 35–60 | Reproduce, diagnose and repair | Source, visible checks and runtime evidence |
| 60–80 | Implement and challenge the transfer task | Function and a new counterexample |
| 80–90 | Retrieve, explain and save | Exit ticket and retained submission |

Installation is preparation time. These are planning estimates, not measured completion times.
Use the reference primers when a term is unfamiliar; in Unit B retrieve an explanation before
re-reading it. Run All checks that the artifact executes. Unfinished student functions deliberately
produce NEEDS_WORK. Keep your first attempt before opening answers.


This notebook belongs to the construction edition. Its supplied teaching runtime is embedded, so it can run without the textbook or another notebook. Where code uses `REFERENCE_LESSON`, that is the frozen runtime exercise identifier; the reader-facing chapter and saved unit identifiers use the current edition. Building against a supplied runtime is not proof that you have constructed all of its dependencies.

<!-- #endregion -->

## Run the self-contained setup

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/courses/sovereign-agent-book/book/solutions/ch15/profrod-sovereign-agent-ch15-b-isolation-repair-transfer-solution.ipynb) Runs on Google Colab as it ships today (Python 3.12), or on any
local Python 3.12+ kernel. It needs **Pydantic 2**; if the setup cell reports it missing, run
`%pip install "pydantic==2.13.4"` once in a separate cell and restart the kernel.
Package installation needs internet; the lesson itself needs no repository download, API key
or prior notebook.

The collapsed cell contains 102 frozen teaching files. Base85 represents compressed bytes
as text; `zlib` decompresses them; SHA-256 checks that the decoded files match this edition.
These are supplied packaging operations, not learner algorithms. `tempfile` creates an isolated
working copy; `Path` handles file locations; `sys.path` tells Python where the supplied modules
live. The code is available for inspection below and performs no package installation itself.
The subsequent lesson teaches the libraries used by the mechanisms you will implement.

Run setup on every fresh kernel. It writes scratch runtime files separately from your retained
`practical-work/ch15-b` folder. Rerunning setup restores the frozen support files and keeps
your saved work. Restarting a kernel clears variables, not saved submission files. Source basis:
Sovereign Agent `444c5f6`. Some tasks use reviewed local subprocesses; they are not an OS sandbox.

<details><summary>Supplied offline setup and teaching files</summary>


```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import base64
import hashlib
import json
import os
import site
import sys
import sysconfig
import tempfile
import zlib
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer, which is what Google Colab runs today.")
try:
    import pydantic
except ImportError as error:
    raise RuntimeError('Run %pip install "pydantic==2.13.4", then restart the kernel.') from error
if pydantic.__version__.split(".")[0] != "2":
    raise RuntimeError("Use Pydantic 2; the tested version is 2.13.4.")

# Frozen, reviewed course files: data until explicitly loaded by the lesson.
COURSE_ARCHIVE = (
    "c-ri}3v=5>)*$*<u%27jWJ1xT-lCVYtH{d4H;(0%lw_wQ6$>Ol31gCA2-32~rT>1<s~g>o21v@X$DY!ByRir~`g!"
    "`iAD^D})Aap|aC95qWxaIrVsH}=-cQqHGSA@eR=YX9d)5h_UDE#@-GtM5JPX>LAf3cP{Bb%;2FW}ar%^l#X7OK(I"
    "GZ<u+hl$dgp(j04o3;Jo5k5Qon&z^Og_#Rv$)B<T~011$#|O1=0P~So`$n5)(-~h^iKb{3A39~($~NLm8J0MaF&j"
    "P#cTv`nlf}C4SqR4e|H*3$t)hse+ehiD4sQfQ#HN*A{j-!bQ(|M8P4JCmy>rvH~4fp3E+R1&jyQZo{r%iEd27>o5"
    "kSn@>wH)Ih(~3e1tE5KYL}oo6gc`F_>rg?t&lU|2|zl%ib^egR@_M-}vM3?dvyh4&g(1FbT&ozxpGbB%@KtkJCx-"
    "1}2VgHu3i?PG?a(>(R;J)BXEK`3Oh9oE)9JIXpjh$2hu42k9uB$AwYa{$X~jhB-SwJ^b^h<I~fBy5pS9XW?x>p3U"
    "xx19`{UQR7^}zxQ}5my;+S2IDx(!s|GzWjE=x-r+X07@%lkZ?XQ9k7AaNWGdNRHjl^pl=3EnbTW^5^vh>|&XRc?g"
    "aHgQLwKG|lF4-da4>iu^k)goWSGtZgoS2+kZX7KJHU228Qlf*n>ff8Q@9p!Bwr6hfQV-B7WO7k021`$QF@E5lUX2"
    "p5%8t+b^j_2Ch0twE@lI`3NX#d-TVgU2U8l1!ek6Rg>$-b)KmO1$)G1|&CWUI`?JUp(i`@M;0<d=i}92<z7b@wEx"
    "q^gUDiFHE#kU9t^A~>;oT?=BWX_<p?mr4uiJRCb@|LWIper4pHWjBl>TT~ujKUUtpy2Ivur+#!!b7cIUHrN^$yN{"
    "8qY#RJJ_IQ_aA=j&C~bsghtrh*|pw6r?3sM&%JmEr!SB)0nDd&)__!K9rXxQYEe2^jA19$s*@p|Uy>!0Y#vSqv2M"
    "`_qGX`k(GG<PobVsvXb~UJX6dYk=Q5s-;(3xzf_U-)AZHo}W57`WMRex<e*v0<J?2gZH)%46GeBr+kmhwf$8PwAZ"
    "dja^v}gn)fS)=-*C?K-r}f}}bOG^K&J>A)F<ZpSfP*7vZZI|J^P+WCJr~&@0(5#HYZ)e!B)jSH2|@QbH-v+93Wv1"
    "nW=2UwqjG2P=WHB~Mt6F)0&#k}GPXR%JM-zjbT6fqu>g4@z0A{e)EmHfcp$~svv|13!cl&6N|qA_Q$PR{wd;U&7+"
    "c+j8IorJ3}gF~p*sp;0olDU%MzUYeAyQ2hSpg_SH%OL#~<ggfA**v&y;Q+eg-&aKBJw%m-wU!50YtZ$&TRt98c$W"
    "vJr(T2@1jv^UF)9x<{yb38kq`FN6wSH3IxwlQ#Gb_@vh2#}0+N3O1b9^?KeZ(w1oe$B1Y)W*mB9@)OWEAm8pN9QP"
    "wQ@=lP?qF%tn#KH+GlASb`1cV1jM3;Aze$=E37_L8x$A~&EOgxy56Chbguw+8;EclV8z!d+=x01pV@<wpr_Fe@4)"
    "4yl%)*MDnm%(MiOVP{M!{5x1NWy!72DlvqxD*Cmo-vVRk|(bf<&=j)XCwRe;jDGnG<3%%)N22l;S_kw2uDxhs=%{"
    "gF~QO4a037`xG){rMC#E7P1TP9o|AA28#?bLkq<nDKW=6>A<(eeGUD9?{uM}VtzK{5#2=#si0T|+K#fNHu{DkwA5"
    "kGN=FKRMr}zgqa!C6#)f(xgHFNp9j+@+1BjTYo+n`=rB=tiQ-wGt-tdL%6%E_Ggyk|}{;n~kG%voF^elsWH`?3U^"
    "U=z4d;p7?_x&)9D!IF|U5Y5tnFZH7^7=pZW!|2CFggz#roHGJ!IA3JUcDy}4es$LS`S9rc_ro{6)8jv0AOC4Fc$d"
    "$jSvaIkr%P|X8IHnh>Zgbrti5o!DvcBABn=el`$*0W_|Yr_SqsQltVFP^<`Kx$#`8h*tDbCPEsICP25xC17y<wzx"
    "B_;~t{cG(>|i_t9%T~Wg7CNG_|%vI(bG738Nh$(1c3+*lWX7#BVei`!Z-o96%IfF;VAhK6QQml$g1)F797I08oZC"
    "^8!7RZNCW4|I8GO^sfeG#V4lvy5rD{Ov@sZ=C~&<9XFxXNxEUx(dP{W&;}fa`&JCyc9z{XK93V(dG7@TW{z0E*3;"
    ">-4h;cBr0O%^PcnXLZ2D?hwt(gaUGoMd8FJ8b@!qH8d%{%S(_SW``4{Z?i!}*Jxm}eGXMd3W`8aRcvLE{jkp&U&Y"
    "P{0wB_>J?ssfZaNBHsb+(+iT{pD7taE&wSFOwqjN0ukUVd{fhU2HEfKR;wPsMO11A3nXso*71ubUccJzPH$&xFXu"
    "gw$AxzF;O_yw+N}mDt;~o&4&pcx;xgd#d=BW~4g|?j0yNWQIcN_N*<~~ygV@Q>KfihX_84yT*}IdsXUCQzLUHV!N"
    "?F%ohC7-QE{MFEb?vylxKgvh3^sf%E#X--7f6SK&0xOhXGFO(tpuPq?M^|o<-YnUs*7gvT2e88s`VK>0uSB@!hQ-"
    "j1GyHf8<4_NCiEG!|9}I=lYn`EW?`YG#C)&03{y7&jJM`SNqvQUl~QFj4`<he;NQ`kS`=pkU|;b9bbCF({=Ht^{I"
    "nTHQ7@El0M0fx5c42M!VE)~PIVUd=0L+WXq9~{LUjYtYq%KA4N;swgx1LD$@laR_K+!Nkf<6oU}gYSWa<T6e|e5%"
    "mg)Fa{_a9c^jEwaS(AS=9h}`6*GthrXy~9>yqNSYJ`ZA$>I3(t7`K%81iI)|41=)<yt~tRP&+xJYuzxexJglDcjA"
    "wUiAnK)?ZVyqjdY;6f?yaXBY>#jY#svMK7p$-4w;u-z+2));}MBwtn+y3(fJUirnXw?3SZ3^Kn>v`%GR)zIY1L9k"
    "`W~U@H9bLGxrIB#+%oF90$LhygGgp=#6~l+3m|`vfsK{@bl~cd;a_BaSnUbCGYu#W<RcS%&K1r|8Zq*t<2}okX3E"
    "e<Rxj#7U4)8sgmA02+D=-1cky#y&j4Py<X5oNw(L+tJ&*mL6&do<pereqVL}H>bp0ArvgeAkyI0)=$-|DVP<@msM"
    "$*<8{>GK0;((3aa$^FR$<GJ*<ymPNTEFq=g7+|P4+wZd8w4$)4K>Taxzdae*)2gz^)M-5j*oL833IBoW!F@f0W@w"
    "<K%kMV@`n}u15q(x;cmS90A;xd_bCtD9K=EgB$hDEBTFz_2ZB6U@=E-1$#0y>a?yV{I`dzssTNy;d*Ml-ViPb;J+"
    "pkeL6bQPm#3&z^h(|L&iP`vAjEdeRO<AbkSCyqsFe)D5|_W!B$H@H+9tT!QPI=r@l=Umd<K=Hx&lponl52hR?US2"
    "AuOO1e6NmW<QA#Hc>S(n6rFk4)BiU-+UBfL@iytUm$yp#Dk8mHU{7YuH<@t(`}PdLH}yCtlnSYmCO5f2U7$5wLq|"
    "$-*u47)T3O_yRb{67<+BG;$M$|+!6w{@)}NJmfmUwM8}Z{;a!~sarncp3And-FZF`dQ23zu!4fV%S}<>^73@J0#k"
    "6AK<dvL3GEA*!byv{v5Rdi44={VOX%LS`3TRgD@X|f%9e!abc<${!aZ7p)y(_HgQHyLQbCCFJrc&t2nz<-1YKW#C"
    "tps6iI18l~QGGh<3EsG0<2$u&i^=;*daK)OyzUoAMJQzZj~cQ-1=T#6F&r%hcN-*c`0OvGmbARhVv@|^24?Ud1ZZ"
    "r^=-@)l;L7IG@*N{`RM;-u{jT1jyqCNMA2=#4*FEpzp{R?8kj?#i&%^>|{Y{h%hsdcCQf8$C$Y;pv6U&7CSx5HQB"
    "AuhMT7yaf_rOBCYQ^=XhyBA3)MMdH)C4sgs0W3XBmn0pXK%?5JmCw^Azu~2%Fu+oIz9aP+_r70b7#tIsV{BfRC7B"
    "<OGl5;f(QCeL0qJr7n)8yToeOGFh-FJDX~C{tSX7Kq8wpheCG{~YqDyMmFJz`GykkZ1>+!*YQ-l`A2%DBuK}qs;n"
    "oGT>BVWg(BsZsI(^vm>2mgz&eeSj%*bFtQeDW`n3V$>bbu)Y7IB`+?gJMbBQvJ-ww}e<gwlCQLwMG4Wl8Tj$5SIP"
    "1G#L3THvS)7xdrp1ekMr(L{EJkUjpwO{V7cdWqnuVAdqNhNQwq<SsXBCX)~8`?#h!wptQ(MNx-L2#(x!U^-A@Vb="
    "Y0U$;2-i<(Ks6{b@J@5(0P*d4t6fT#*yDr|S1rja|ld?)RBih!W!X#;^d(JF@t6aDNe`<t~cLsx~<E9k$KARDecb"
    "7=ag^Tuf`n>vi?oB3l4JX>CYXRAYa54ZzBZle^09=d@@fx<h|ODZ*3h8DVz#P@(GJ+sX#xcICq0=+ptJbin7x{_Q"
    "0vr9)G;#wUw8+bMs?W^Dg;`<on&3L9(j=~1?jM_T5(AXm_wj0P`0P*~iE=c}RwIl%rmD?hQ(LY4Vtv+-Mr<=Svbw"
    "oeU0ogP({8`=T_f9ujfO~eOq_5uj$;q2D>uY4I8Ncvg$7g4U{~*Ci$fad_sC1xl^nbs^qbd2u02If#;SQ@p7ba_h"
    "+%e1MtRl&Al&#vkeD*W!T^xd>sd#yUJfX9H4}c@14vb64E#i+M>h9SUMqM_ybMd5MqM`*FbA)ctY6fSE@i?3%|7K"
    "GG;c<Yd#R%G3MAPa0FaR>tC+)=`9mCQiwhKflToW9Z?hjDj!7PS1lWXdpCo{j9rHktuJz!zxw1=c7g?UfYEF6&$q"
    "=fJ(<z>m4iqlW&iN32iM`lRH1Qf^_p3RY5<IaTRbYU?RIF&2gID}Y)fVrbo-S~fpi}_882ALeU%+Z>GGlQuILm;;"
    "=af5(2PQ@!AQ_hD`JV-LMT^N{0i2}V|f-GiF%t}bkEujD(H|Z%HKL}z#;i-w)hjOrxK9o07BM@fbhemGxL5Usym@"
    "ekxU1SbsYd{SKV-kO4!&g&{t{RB8@@$??U(dzZ<P{`xd}10Z6!#i`ya^W>JB08dzC~Xq&6c2X1-+eU_*%IOghoR("
    "@?Yut*pZF)Y79xEZgP!z&-UtMoT3Flk6e63a+qd2Ha>U_86@!esJg%DgIE+#U-ic4EG7H0OL4tA&DCtLvYL8{Okk"
    "X@ptDZ!K}<)xV!1JFM%(o0rI=AScUvvSx`<^+@vYDv-1vIYACWg9{(!2WL0n_}UH2oLaFX4UsEu6vO_HfA^HMCi*"
    "JzJ~Nua}XIANq7BP$%v)0sv%>IAafhNplR$S>*%QCG&lhKmVVb>LZ<8;x>5OC~~mn%W)GYDeS{8kPH(HG&JpuZvD"
    "9?E?Y$K;-ViaGfb1($+Z1(+fpXuGoVN$F!WsX!(G>lL-h7`YFi}FtT9}%{$a&$kC_JN3yo`Jz}tgX(}?teuPTSpj"
    "IbzI@C!%px&rn!cq@$)YcX1c;rQxKTXMyiR@Nti?ugU;oj7!BSQdFzw;YsJhYT4#`9c_X6~3FS;%gP!ck3&)@k~+"
    "`7Zx<BWSl-mrnXQ^ETHCh;J8K?|52Y{g;?b%RVF*4Vvh(p_dt5nU(1VT3)EJA9Zd;^%+JDeyZlsaOpSFx(nz$7Z1"
    ">Un`<2afNIt|vA}3BLWIE57s)<6w}#O<$Uh=fG}r?o>$3Dzt2-t`!Y!=SYiLx%<`zU*`dN;}d>t^_)~AzYgwXtm-"
    "?oDC6;^GS&b>Q4J7ZI*bR~AspATQZF@05O_wzF^*fb3p-a(=bK&)t(=x)~SyV+uEsj(}Jg^o^sd-vw}{1`41+mDT"
    "jwO7>zFl%^5Qrt0GviTCOq#fAyY6rGE!4$|PaCNwQ=$<u04;=ve22B%43E)@}a6lSk|2d$l3*tiw#ebZy8wKRk7s"
    "xMk@<-8s1sm!t9>$0-V?gfLz<m6hsCm|;+u9_Hr~2-M!<WuLZWi%A0~xW0Mh$kU?d70fVmqb(vQ8nNIBO0{K2Ux)"
    "J=vu|Z^eWi_IPs}C~C_}=(>#Kald>Ty4Txu_Fi|1p(BkTp8U0l7jTU1M^w@UdV%%H`Be<S@_S_~bFKq1M8OlGMy4"
    "?6k=VwjSyoGI3R@cPCHmbERSi9L@t~0sbyk+=et3WDv9<X+PcrJ=;S&7QuuY}vMbQ?MFR-a+T0X}o0=puCB~6dQ7"
    "R~b*K{K4)y&@08baq$6Ta|q5is_PFIyR8o3^V$Unp+-1&|#NQOijP9ld6#~LiX1v!Eign>8TGNsOwY14(cZG3Wlj"
    "geG4l1e#6s-*j1Tm8FnC4KxOZlkC*s0*l##56@-Uhy$~RJ(Y9=dQNKADr7)fPit_|81xO=$YapV+^zsSRb*vAa6V"
    "Ne4hSCf2z$r*`BuWq!bLU!g96B5#DVoK?@rZ|z?oTo058uQP2biR&zboIyO=}zNx#eV$Cb#-NtvUT61}@F{@A=Iv"
    "j)VSU1Q;Xp%y-M0ub_VEF&#x4bJ8x`{VQc)==ijglyf^F3`4X;`XQvZfs_Wf)C_YW0z<9nJ8b;w<gG-hk^(u*-e)"
    "Dd-?aN8GFWkx)}<0}yRIUmh3~2qo=w6!1!JFSK^J(2OYZ?1<(HwR!6%#xx}I*FV_fZP1${rm)}(WIEs{2TY;#^6U"
    "bA<u6(bebi)bUAOc=<UG1+|4mFw*I&GFGW47Y#@{ZJ2nK0Wy@u$d4zpyn_J-U%pY4S^o-eY?1r6XjhmYV}#9Z#gY"
    "PJg)o@J&A8CA$nEywgpX!?XY+kN4zf=;1EgKVWnLaQ|gHCrl4oPVRu-EJ2g?ag_1zZNl~C!-yKg`$V{SON|Fu_Y?"
    "CaD>ETP~s8OsdsOE`gE)gP8H`ca6Fu#ZSuuXa7UA~%y3(HKmd?UIIe?(;=`qaW-WxW~7K7kt>BO)An@Zm}#wTDNP"
    "+sEu-kr_pF!|d)Vc*WPt3K*&i(XH2|7Tk>kv1NGFOju&PLri4Tb8=D?;(vN`a`Y?8(OR`&DGyAHb0mV-46Tq7-Z5"
    "tRq=;|SN3Se}LT3$)!cwim!!!$JT-~>>aoF){9Cpw_mcpq;?H;on@PYqAza~n-pnMR7DMVB0AdXf`Ir2T|7pi-gy"
    "+P}Q3~_XLhRV1B>`(#{eB7hm&hl;i;(7}~`s%QH8Ai5=Vp!=klrD_<+lKOrhK4;Awy7Q>5a>SYUrAT-Bv`Mexu)n"
    ")jDhF|2Cc7g)OzQEOpymo+8mLW8!Cntt}gWxcxB(R)c<gakHu^?_nh-{+@yF5fCk_XL8cpoJ2pPFoAY!$GS{Zj3-"
    "W~d4W()GfIb;{K;f(X7#0%;IqD+XNnrpM0>GVt+1YN(cv&;CVH#Vlav*RQ^@4Sf?s!+@z?ucT4aPiOMl!IrEY7-w"
    "M=v^Cu8B>iplp2nv+lJ<x;Qv*T;&^L<4und5%#$FP>)5<sFe*qpdvq=c-pA#>C${X4ODPekM}5-jE9%cKH)PO{l3"
    "!zIATLJ=T68sv*9&Z8ZIxnXMD#m9F=lRUaslW<+B{n$emmc@ZQfrS!|&Oayb)9;&6KW^Y3TKE!AD&rpS63z~B*d^"
    "Zsc&^)-+g3jd6+P!w+j)^ldlY#DuRot|?uLyv;ZdnaKE3XC2kDL%4@3OwI<IxiRS+GT<WoPScGB;tO3nxId%i_^V"
    "VGsIhWy?`?&kwytiJnC|-&Tk2@SisV%TgPsRa8E`H;5PVVd=iRB4zFHUQL<iXIk^W)_Amw4@~=zeWrewG^`(-tmN"
    "i!qeby33A4d?B;Pmc8HEaBRLAO?%<~!vwN;BloK1(1iMXki67<^{ObuGGonD8n)i6^CYtqX6yo}{|#l~i{-0mz%="
    "A`g3nq}#A9!hUC*ENem5ah$wPqN(&K!2$qhhAPha-MV6HnmtLd{|yqX-(b(!v!~TvV!&rj7%8?;A>GRzX}*Gd><<"
    "}_NAdM69QV-kV-k;aq`5qAC}4+c6$1rIM<i*#17!B@Jm@}_19~pKFQy1PH4Y0NV%S<hG^5+z+^Wh=$={J@U?(uX_"
    "9UtFBvk=H4Q9$Oo^c;EDx$<B>-9NB7P%?j7sF$3!nyy`xlXDh7$(o9W9Gg5IOlL#+*3~?P%92zF7i*Q!t>#PNDQ6"
    "D92KE}t}31Cd8dkQ_3|7#lE0ky>2L@vRAxA$>Q@;n(hJX#D)i7>zK76(+6M9TG`u^|ky?3n%x^FV41vDxy0PLbCJ"
    "oo|{CAn)GoL4i%u`8v*c(Rw($k{r<=@0950QNQA)df~VyyKjjxdiHeoQx@kG8ECmH>x6!WjQJ69r}ztDttI|6Uow"
    "++NSlnKP{yeOR1L^ewq`pNoM9=N$T=GeizhdZS2=aY_s9FF5+;4%U~Igqo|HB-ibr)e3%OO@LaHnH&zGF9}D<zeS"
    "Ew-a};)jz`BLi6^~6P3K$EnN(^43L1b)>3^Bzucdy;HOX>CQF~FYFQ|FAg4H!Du1?@ll?=AmWz;uP4FYqJTkJH2w"
    "H(h@lW0riE$Ol;EMWd%W$~*h{Wv!1hEMoz6eU695$6MxsdSa1*5)&6mMo$tZtkn%JP_^bUW)99y|=A;!-;@>G&R7"
    "N5%V6^;;3?c(l@G!5sSrlNLw7%RACF>Ri(owL}?(=<;ra1ruHcpXwEg%E`-Bsx3&~(b#QP{S9}3HZ<{|h>*l@Z42"
    "mfUzJ^u>c(Z$xaz$i;NCl2y3XS~BqKX0u2Yf<t4x2tDmyjqWrAb!7T=9k<TRM7{-Iya{KDMJ+qYli~#O{{nUSIju"
    "6!%IX+|Z2WT1q`=QKHv-rPJiV@9=%D;ma^jnO=9<4tum(&?0BxfKzKVf_7{B$~`kDxen$TXk8VP<4CH364i$%`=2"
    "O7lE~*^6#V(i@#%5ESHJuG^!V`AKc5FDr>~ArgP;D%A-Hh!U{GW?N)^#&P!@$R+nya$)Ujyaj)oy4bYbnV%;KhTH"
    "(o!DEQXawy?puA2aBG;F)0$%qzWC7PaHigpJdxJ$-HavZua^~!1W(cBXv1w76eJUgL=jCim+_sLm_tghST0PJibr"
    "G6&U&<ue#CELX~SBdDiQlyKhUSpDG6(d$Ih1ceP%f-jU7$&vG)I!={b3Jxo37i#<++1f@zR)nV(hmf5}dq1ee8FZ"
    "qGJd=9QVTmZuzVul`MLnhIhLmM;%H;rTuhmc5<PmIl0Kwt`8X+59cEAk%4DJT+tfBWm(lRw{jlI5Hozb#}#%E{0m"
    "PNwq;h4RFUQEl}y3b4=z<J0%aB<eobvu+BfL0k0P#G^}9(5K|hiAfdVeDqYskDGsdgPL*exvqA$8?;>|bU6qs1@>"
    "3+D>1ZG8ykvgv4F+v^I_$59!<NHFCw@DsTB1R#6m=zdja`CTs%oCXah4CDp4Wn?pB`YEKP|;LOoX(+0urZhK@R$y"
    "Awe&AHU3vV|X3U^@7)&K&3BE!`u_}4P=E4szk*#*c?0HTfKY&--a8HXhhidqnKR31CDDDl2o~@0rD_wyshelvLFX"
    "Y*ia0$*S>x#w^)|DUT#ozB`jz%OU6W?OBpt~Vp@Q*<2DhtJONww?2XHk&o?wc&VWM&t}4$z=KFvhPP1k_`H;*2MR"
    "Cmf*~uS(K41UiZSU|OfU$e$fUf>=diY!K{N&f;x6J<M$21UWXlXYm?~YFo&reRzbPvr8_70mi+yW~+Hz}xs;y4Y{"
    "OtL7shA--LlMxBhbIga{;!q6yiG+=(RWIE)H%DDOrxQdZ0qiz$NN`g~=uWeQoD3!a#WSGNiVEkL1P3IPBOBlzyG}"
    "=qT%x*eHCm&*@{5(m0)2}!w1|dqoWoA3SiFjOs%XsH_*UtAD&<a987Im-nUmjQ{=2*%g?7nw70%!nGJ=blN;A|4W"
    "Q^1nXP5^xprSgAw8;{&6`EtwsX#d!;N*fZ8YlBP7a+jgf(aH{LFd{mqZnV+8z!E|M9Ipni^ww)>frpw%#w_=P)xp"
    "X#5hR`-e{_<weWYe0_(DxASjGV_kRV4Z(q4$p`B~VFC+$UUjO#`JlJem1hQsm11LrS`9&dp4Xxo~rUUPsrOeBm{2"
    "RhR^2$xTtECH+h#c|RA9BC~N^Y_)2r24M+cuy&^T)Inb9ty>m~S`!rCOkLG`+5`iMIEAx_riz+%f|OMV(<sM!f&B"
    "?)@S}B(V!ZJ(6uP-oCckGEub_JG#r{AZz0KGe1Q1;WXbD2Ejb2%KRkX*9%ZCJ8UQCy)a`Tuhx}YszfV614-2VUw9"
    "WJ_az_dRinN{a1o@d8yRQiWRCXM)!?P(&M%p_s7AV&_tTF(PSKJ((&U@!{VE%z${wt6JnUEod>^Zj0N`K3erH$=j"
    "*zTQv5)e9DpZ#6MP&^P0tf-aqD@5;POrdYY*NbtubM)H>C9NCDQ~fKA;(qF(9?Sl+;p{M>;XAX_mY#y`Ao-8dZ(s"
    "bjb!;>-s5P`>v6P~dmM3@p?{^i01N(%r%9Hgiy%`ol~EV3#O+N&#mPd97LBL~%Hy~jWsAOW2l=DB%;Sxu9spPWWn"
    "Gh2>p@pGG<=3qgtS$@<_cM;@k;2i>LeS4lSXih_PDj&eKHI`Ta04NEI0tRY%x(!zGB>q$`{pRonoG{qVpvao;_Zs"
    "GjSOz&2zSDg0pU(;Ee9p<D?Q>KNVV4Iy6rzwAJ&K<(s8Q_vhp%t9z4=asT!Ig!W5xIuFu(8AQ`n_L#yFHp_7-2pq"
    "{MT1or$UFJr)4d2IA_GOZm3o%lU<MqGm2~6+X9{;)UPImlC(fzv+WH_8UB6NY|vWfqx)q{;->%dTx=ZPKj4}P?oC"
    "?etw$Cu18cESW>TiKnEF23%+tN+5=Fh|~X)MMjS)@`@Et07<mW-%F$<0wI=00N|()h|k(MV0^W?_M3A9|yMQE@lc"
    "oJ3a?E$AXDnJI{@1?~$I8<TFWcyLLvzVz5H37}--{e<0HuZn`6aAXDbed7(G2Bz=QeC2%!(5OTaY0(9vM`1opD+p"
    "@M+bR`6xzTNd2*W{ymZbn({XvidG)6JDmsoaS`>d>xW@q%q{N}7@Ac|j3fW?u3p8VE-~(Xa|!LbhtafUE|j@reVF"
    "7T)YDzE-$VTLvuL0Q*8^T1E4bQuX<MQQskb<{w<-Rab=jVNa*RCoYF*bs<UeFSK)KrWhl~DWod@sOuA0ntIf1=nJ"
    "7zX|c*<bc`Lz+3lKx8&^aqfOm27F6@#ZAYDrO<Bd^z>*lDjR#-23p`cV@$I%)0iW(WWN;P)pLb`)!McClR4~7f<c"
    "?C?ApX^nci-INOmYwBe;>2Wv_YRfVhzq6uQ+Hqa8@*q2pBrm<?gN*y<M{H^Y_BuT^(bFBgGsw&&y|UnrF~lB{$bd"
    "Hf`XUC`}nTILQc`Q4Bj<zb&g?Hle%jKjtxG*mY)!q&VP|B`OmZS<KIqCPR{xF`ET!Dy*`!fWruJ7A%7k94&S`Fe0"
    "J}3$*3@)8jBOZeh<NN4S-b2lm1JI_StalHhS~sH*VN<>#=(F{cn_8or7qVsDX&hu;FE#a|NF1+ES{Bc1Ow~qwHgJ"
    "IbNVQQ35zXmCaN(RMJ*5bWo>oH3G8sa(RweCt))Ke97+AHPlSacT^hMUerZ)mkFGrdJGR|V=Q^%Y+Z;XM9cpq)Wv"
    "`14hblj;NNw(KpC7|*EqdGnXd?|RGX81{qDHfD4xxhG(y`RRRSt}9M0ywNqpNAM?AMtsRz|^!Kj#%Ad15XB^D)!j"
    "MGUv2SI26*y_iicF^+VsNSy^d_Z+lR`WS)Bn#dC&wNn!+2$=GYiqs4G?5RpDl_O96C0ACT1-bin}V+@HTS}3Hk~E"
    "c$)x+7Yhq|X?-+Eyv-#ZDi-{(SZ!vijEG<`l=OmetR-RT-`=Q@={Bw0oIQrc246;!iPiw7aYtxy8a)Uy>dhXEZos"
    "hvJGy-1+3#_P0MMGs(;y{lWM`H%ljm87iPT<8waTG&RK$LHL=9-iO->&0^Yypi@EIP1~D`|xM;&OUuipm|5#Syur"
    "T!+{{NUzxNl@D=NbLBm*Qe|!l^R)-e*WQlBeA$P8p=?`n(4PHyE)nq=02GF*buKR_8$qFz@17I@`G4Ab&7Bt2_<)"
    "Azs8sBj51&`UfMN}Q&((0^cDsZ@v}A2fnOIQZfKvG~pGx6-Ki9O5G-|;T7abw!U&>Tf<Bx*3J^s)3X7%jl5?<9GS"
    "s>d?08TsBa(eyZew=Iga+){8=e@aRq8a~rmRgFJSdDF%(6VPIST0{Tmi5LuCpjzZvsyM=+F!2qHaqpioB2P-Xthy"
    "z2VYCh2v02adfURGR?DZpY&+KL$G;5@nq1P;eZ~8#cOJ`p#oaFGmM7t;5Cn`NZL2a`sv+0LCCSxcT?=ev&Kfs_`{"
    "l~a)DPCrTTBS2)TFLjcgN{cazq&{vkF80I7KJmifK|9ZT*qw;}cj_Fp6};=CA=`NJKTj4;A02(S2EW&dyKXy`#`Y"
    "s>zCzE$T)7q^K0_iZ>X=;be5@s)}t_^e^kUu<vzT*za)B#vq)+E`V?jM>+cdB15KP(i$QU0N;{gWJ?fI#V)J?3{;"
    "6?x8b@Ky%sDd1(s>H9>X_50(uSi1bH$JCxGc@kL$vqBi2{*K2Vale0?UrkKjKb)h=^95CW(^MguS))^{n;^}B|g5"
    "T;*cI^B>WlrdVtuypQ!qVNd*-~V<G0IkYuD|&LyEVS!1A7KP5k`#_w{-wthd!nAGUYul(D`_7b0mRWmxZZ0UV^3V"
    "qYNze_aAQMlS>YurFeqTk^AT>Yr?-}O1hrem?&*!Chd2H%YC>Ke|MB+sH*f4Vjv~Zvqa5w+VCG7dglU6hgu=yGVW"
    "w~_0HB#TzdwrJp<HklcW!%NZz0c9V1A(+l}}?J7*pTzVF;_h6mYEiu|$!(BpyZ1^@l!g=JRRi#f$dlUK6I(Y_qpA"
    "&jtV6qf`a;I$sSP@$T>im2|#H<5lz95D12kZmvngtLS&>SUSf;JVd)?jh!TP{dH^7{7!W(vwMe&CB2%Pic*MZ9zw"
    "~-cS!VFwWowAB*!f#7{Y?J6-IY?2^CG$=or;(^I#VXeUXX4kKoW$P*blOMk6CV%HwDNOY+qg3or=a?svR?1!ZZTw"
    "2bHI29bo=Uhb;@4XR`3q}OM06BTgbh*>$LSo9^wIrxlCaGkDWL{WnL+1q=5XXR;CX@;T%#G837RW&N=J{6=&Hu3-"
    "!0Qc_~fn9%QJ&8tr1#N&M1nX$ou0#4gGqm$w(ox>m8-d~f)!n2rkh)i%v3l2PwW@VEG;nbyD~{_|>Ua$QM^u$AQk"
    "yK;q2pD-Db(RVFP%4qxugm?pGw~dNFw~*&QiV<oHE03xuG?8r^0{5gblN<>G<<wu-jT)*lVn!H}mWgxg;rWTNe1m"
    "_o)1(-n@$M<x)z^dPP&U>&pACyrq2}<?YH2s_|GSRla}TeXH27752%2N{>9v+oEr}uMhRkXSiBp%T`RVye@I8hW^"
    "tSO^}g+ASv7qQ{JwIFcjD;gr5_i91Y|o+k&$C5=i)4aKt`Y$O)3uXpl_)C4K^AVrA+2dWH_|yvvdBzwG@Fj1v0%+"
    "eCIv7lbl5gc8D5@GBEyhCT`c+EEXg-%+<!pm1u(>PyWZ<tHk9rR>U=J3|dI_3!aQm*TmHUDm$^hf)L<WT>0FEI}t"
    "~sj)7OgBW0qZl>r5Hv#q%6<i3zSvZafT&~$M;>$qmV>rz)$nXkQ;x_jxxlQZPN6{K)Y|TDu`!#B4q7~W5l1o-@k5"
    "(>l3t-`EFw;640-v28|8XJ-(AuACDN`#_{;$mM73^ZdFfOqUiS?_sk|psJPn5#w;!zyp*=l7ZPbM!~;rQWN*+L$H"
    "8dUaNT;XaAS1Ge4kX-V1MILJ@x>=RAT7#{sKOEcYMXUA6@A@P0=il;NzJ(i!z6O=EOy`_@vkbWwyoXoBuN6Y#V!R"
    "lIl&S*t(zKqhCMs5lL32B`XW9M4W~&H5l^67zl7CqL#U>pEm^E9~g&Y7U9`;awjW_ZAGPi>gX9ExQ&>7E^hE}Mn<"
    "iQXX-@hf>mDe*uQc7WAq5^r)$e@fmln@8%vFMF;cyx69j#8j{zk9&=*sly%;D~_v;F`Y#wAJYAkxzS;-co>B$!X_"
    "0GsY;umHN&-EGnA~Uwa(GaJ9#um`sqtL^jU*vEh=YK5Adp?f6RUW6w#s5RORx><Y{ENbW{9B5xq3n=eD^>$olYH&"
    "8DISjLukn>pUwdDdNp>T~Bt%t4uu-+4x9*2S-qe96e0kKMIiqN_3!kEyr>HA~&U+$+pkQhhgApMELtD1jgpf`J<v"
    "(1y~-KgiOTx?z}_4sYD-nt_|j+OC2(Bh{{Bnq{={fg&+=oBGO$4tR>Icn2JKy#o$_NMcqdNz+S*!AlJ(hdcu8G@W"
    "Fzq^*i#1j~4m=jJQ=1w6R|d_h-$&u{^FJk!4c2R*e7Mf1OD_*bozO<Sr3m^8-M{J+dAz^18R(LF%V4uEKb9Pu{P#"
    "kM+lawGVBHv$t$Y8(+I5p~y(2kAHt<mevLpTL5x|3=3G#So!2T%nnj0#81J`O5WnZJl1Uz<Y`9nfXKvu~^N$pd5*"
    "QyDkO?WiAG%%C$f-himv19Ow++Zh)Yfkngh{3p{-BXZDFaSw2UHpJaRY1N6!3xFZ-@^6D#w$bYW!zf~~)D=iD|qM"
    "5dj7xG|DnhOk^YQ!tJo1?BJyGy4<*<EJ>_sbme9i@9Lc2Odz%nE`ENhl^>`$p9;?PA?6WV*<7q_Uz>)vcKdEmSt8"
    "^mYQB-Xv4L_&61iSTYO}PF$nt-vaTe1~QHU2<ZT)qi_(DzY=;dg@Cc9A(r#fiHzGV1IsqQocX#+ar9vLdpzCIDpM"
    "#`AF0Yc4>f*$S!5;GN7Ye*2@aA`5^|oihHnoWGOusuBC0ZfpLG*U@3-_`xToftGh5%n#Y5n;l5jL*E40?gcKiA|Y"
    "81^Pd?RX<cFU_qX}3BGR{@Sf_7;^Xi2E9d3n#%4rAbt^ppltgP(o*vO0qdL4?>LMe!R?(Al?Ic`T`o6|A?yPGc!h"
    "hZ;G0{*sO#SKS*<fR}Y0LcJ!$c9IJ9SS$AL8+pCnurMcYQWoZM9OQ~`$(y%pKuBLY#Z@En;v4~$hFLD3Yxz|NYWM"
    "ufIj^N@g=9c$2T*e;D9>fGFR^MOcvYJish&Rx?QM+h9A9d9NR2nFP0Jl<+2G_2u4v^WIdH1<`)uYHp%OsXn<dYJb"
    "^*Hi|DQDz1rAHDo<n{99tA_r%LcZ1Oyo{!XlL3Quc+L5Esu(@pxOqDR_+tIeLo;GexyEZsDOBM{t?ti=tu~Vy>z("
    "yARq5IBUjQI)n>?gmx6B`TzmPq}=JKbTA-gOScD`Lgerx_6CbFsTYK|3aMray&9&MzUPP8r>zZ_q-mD;P1*`LYzO"
    "vUMAIP#e5KUrn1&7`3n?UNuV-MFitRQ_8`F0LVp^(s0$Exv>27^b<HPZ5vZ*R2BC1FlOZyRJs7wCizy=7)BdxuQG"
    "o(Bo8<U&S)PqhTcrMvEcU%#}DGstY1}s4_)$s<c*i_|QrrM8?Uf#Je~JC(pQ7y<4C&aty@8WsAW8SQ(ThFmf0$iq"
    "UPM;J_#OxJRTa#7yTs@npe0mI)#X9F7**P1o>sa~W%{DE>Bm8{eL)45=NXG`Cc#lk(g@V0H!g=ZE*V_?Nl8C5tpA"
    "Z%Qkrs#1v0GXN>-N0m1*$z`*sDz*xSZxCyoYj4webNn9Ib#;_lq7tLiL$cQHtE{ybIRL8&E}f3qj_*<xgukfrwM5"
    "lw={Rkj>w{FSe+y19t(Q&@rX7Fj3F%-c8@~z$7uOlGOW=VnCgF!L8KFw2`QMZgjyGd@GBZ!Mf+_=|vbZ@g2^1_H0"
    "g|u#3GPPD7y7#+NG$oZ)ck1Ppr*<c=d`){>RHpuv$j=QCJGj04>@;qG&xnzi(^|>LriXuU|^U873*E5o-@C1$k)C"
    "s6`Ms>Q#!L#=N652B{m88GOw9p+Ze>K$t_Gi%crJQ+95+EnWyPS9L`2}lFPoB8V;`@)}r_5uxRn<meXVPLXH1vp1"
    "uCZuOMdB%Rce#*H*n;n?)blIXpJ(p^EvvJ4?E=jlizn`Gk2gm42Rh(7Ts_GNC<{x{uO06LT=J<p@f{Fq>}xjsuDs"
    "afw3GfH#*yr73~@U7x1rfv<px0AY8hpno<>D^U{J6=PX!9>FUD5HHiUh<+t@(K2LtY|8^By~Zl;Y`hg^>F>mFAWg"
    "j2$jR@jOM9)Y{x;+q*7o`J;oiJ@tA%>V<X8*4*$CW2(#v)_$vMoRm{Cl88%i$v$`=R!S1Lfw)5YMXM!2(=zVH4V!"
    "Yy4T7f?CQ*jW!}v{a|XudK~6P&7}beo@7ym#g8;UNJl3GrMYpEuu9n`ReMc+Wm6XQK=uUCwI6$afPuAwZWAyTJWj"
    "@tiKm`+7jc(X9aVVCEYW@<?}<UjAG|H<#>S<6ft_eh*n>}dUNb<o2YBOTBiZIzoEi{4I!9Ei@6Gwbd*dUy|7R%Ch"
    "tS6>OIk5DUh3TYEG{bOJ&^zltcOw7bmQss}f}E@>ZpqupSjew!h4cklr$K>JqC<*9qGGhB+uxBh2;SZC9mF&`-Ue"
    "VkTp*P9=4nIzg*k?^c?<&POLo*+-w}*XkI5sde$OiyN7eT3#u8$rm|VU(ztIu=m;Zq$ztQPu19a!@glOXmD$N<K0"
    "9%4=Yr};#q~6)+|+&n`jHQK#^T>G)Kf<C|triBvy?z0$)qI61pKX9(IArXTP$AmM5(&w;XOD)4(_p`;uQd<%Qp1x"
    "EkvMbw4^{jiVN%tM*kjM^Sfrc4H%wNf3vF8@OEQh^oIJhUM@EPP6R6D_2&UWmS^VQz3aQsYd_<s6xi5%flLvG(@%"
    "-t3e6~qjC@hm3ajaCx>F8601{z^|4L&ZNKTh-3e||q)4cu(gi)UhOXuO+tEAD#Gex0prW4eAJiJc*z9)nV7q;8Yk"
    "y4h`rB0DJu+c@JzIPH5xAHhmgvhZ=CF1B^kYMBAHQD9KK{@Mh7~I^Qu>{9c+d#WVQxnN-6h{<yck-7xk1yr`As@0"
    "`G_hOV)|XINu$0x)+$9D5)b*8le6>JZ;pGfPL6*6?fC6^UMI~!3H`+gMTkj9M`3Yk79hN%WK5|>g4fp*)ajy5Le("
    "37F0Zqu&Zd9)?048Q8*yN+yZ+)1E9!7`mrnUGy2Ik)Nye4W;a{aeM%bTNMu{U3b6^`VB9At<qsGJk`#GHrFx4pZN"
    "-i-lpt^n7^UGii>?tO!h$lmAs_J6Q1yKQ}Aov)V&N3xdkG!xmL7d<IVb%dg+B4?bm1fmSs#WQ)Qh8+;<jjh-?G!-"
    "Ok_c!ea2yLIxg%QZ8mQZRr}%`d`{~|Qir75@!xWCvYokMX(i;z^D|h87et?~;I6g0z?#^F|Z~79V<WrD3mz|=Af*"
    "Fz7K?rmcG1vXNV>lcnw&ppaPYM-2!y~EtJx%nT=T=?*=c3RRh_(d|$@n-=f39qpaby>QCR8EXJF&I^kzw;0X&9+Q"
    "bW@wo_!6DQfbp{VDW&Q*412vEiblPjfOwX|=&`v(eBR{8XzrjtzL`5BiYK$bWvAnjB>24issa0QaHezPZZMwi<<D"
    ")<<lVyD<oPb%*VoE_QCNVv*ozI~1+AL1UrUe?enp%=zhVtjW?NyjszRo=In}9W`XI}ycx2f&RiQN<6W7|t)sU6>n"
    "M-i3A=T&5zfH$$Zp@tzySr^@&=3=s5@NvM=i=zjS0;yNzhN^&(8J{Z21Msmd7(Oe(dI=X;l(B{19I<2xXUaN1uKN"
    "h5EN_>2G`iFsf_|uWOIyMHE%HO34vo7u!JhOD9awuP709MVJHS~7<KK}whnwootiBE%S%aX<a1MDCb@E4Flq5-;c"
    "FZH<cQqbu$7ScO4gV{bDkB8*Q!SLg@Qr))CEJ6#iE0^mG;tM+vzZ0B#$Kn6!ZOmn(5-(eA>7hGSWTH=aYw3!3Rgb"
    "oE)9JIXpkkADO9f?#q_Gc_qE3<Vr^h3hW?8*Bid7BryP`>`@{_R1(}5D-ir5eDl;{KuB!YV_oQuuYA=}Wk=^Xvvh"
    "HN!;&osyvm7I>oR0R>c#zg+!8a6V%uM1rd5p7B~?RC;yV7wkCQV~Z0`hbPtJqW-`~Cru<ox(A|(gHgj50{DT}7b1"
    "oKEIW5N?FCd$m~Kj``5_W;4UFASWJTT1Zk@a?OgPX2H2^>6Uox^#dzNQx9i+Dg5g9i1MYAN^uOKs>o-uW!RChb!H"
    "?-MqrmW~V*8mNwmGSs2}V`L7zSt)b@FkTJe$h0ylq)=GH<ZMHyZ);c+3sF=qMDfXwGuSjcy&QxMHw&ZYogA^BD;0"
    "g?-P$SJQFDIDbq^pryjXaZ{zepz2#ry@TH^}4VdA)wYMed$o!8fi=2DsaT!=W_qOvu0O;<;?oa|6{;_MT#2SSAie"
    "d%t*o)wTDr-gv%9qURlUD_)>m@jc*$XAfl-Y+0u!B2B~M3MB7gkslBs?8?7&e_3~u!5nWKp<255kf+`-e09NS`if"
    "Hy@B@R&I5h9*<hOTkj-9x@Vj`kqKgy|>EA*0|C_xhl!kb$Ncnda!?e6SsZF^|JkpLqrgA_I=l?i&tv+7CwhcuQWT"
    "nhagD;FJ-oEJ+=1?c5C5ahl(AS9q$rNfVWaz%GS3|&SKj&B*`imt*L4s@VH?5u}edzX=k`?<Jhx0*YCK2W8Q;&l~"
    "I?ELj_$GtbNe|vo{o+EinD(SPB>ZSvg2FW~JbpWp?=xR;*Dp_Jjx>+2w;qCt`6ICCv`ig~$+M9kw{AMSJ@k(HHFO"
    "E&|I+!jaBRdaFIOvZO3fWBOnYhBm;<+XJzJewm*a%dy`!(~$(6@9vqSlY8o<A85F<k2GCY}DqRf1Pht@GZH!#sC$"
    "ba-}r*3g@_QZLDv9Ja@1EME8_RvM9IN_pj&t#tcnVq00w{>%CKyWbckc{T32_UmUrjFb7Fz%5`d5!-;Yrh9u)VRw"
    "wSt@#b=-;xaN+Ho`ZX>o^aBtCRCaerd<0LHI_yPA7+^#{$0=7i43(|A^^H}!|^Cl%|!pG^^Rbnpux6>@%|!kHvfE"
    "M_U<gGRvZQFSJNGsyu``aYgy#T6e?J<e}uy^goBfA#1l5jb0LK>stJy5h63HJ%sNKG{UZ0N8ZaPa*(Q;bl52C|oP"
    "{O9?fTyIP4HUev&@s^_*fq(e1vLrE$@9Yy285=}T(G*@z3Fb<=*X~lzlX$7aM%U-40Ec;f~roa=!B>(XBU$^mOYw"
    "3rIaWmXQ8o^CGnv(Vz`79O|1PFvoao+XBaFkeC`ARb-JChelHf(&=C_tukgSD*|9PoId2uMx%MRYF!Kq2x1+yfjt"
    "LmL_35aMVGS5_=50u(z)<NDB53tvQ9siK#y2Cf%A*Pn7a!jL>;JWTfK@&5-r5Y=Z~rEB$+bs@AitrQ~0B;!#gX-`"
    "A17P%FB$9vrfsFcjcKz5gS5PgF-X1v2H=YA%|jPv>G5JKc)x|(p;420|3eQP=Nv9-TA2_KrnEm5uQWowzo+w;=x|"
    "Ks)XpS{!L|MUCn(_GTgbun=*s6Il46fKFR{y{oJP-p86?ab2gR8*J}qn#idtZ6kN_ZoKlL0$wtqaP?hCwNkLz#AX"
    "hP2}Tr+ClO~>@xQvd<rF`A>T7*_>@O5jcrA3=nF*m)|T$IkH2Ph_)c|6Jtfy`rW`PP@eqIqam@sMtDn_vwHAFtNX"
    "-gT^l*=c%p<qK04|wmgO?4EMgKPHIFV@_qUXKFaT%9YK%XDhi#xZN72*1#DyVYZiimlqzzM!!bllt(UWgaDgOuBm"
    ")6<~_4e`xdh9T^`qT8cU3HPi=0S9v79apAYMlx{{?ShFWbXQ{%sk0vEtc`&#s9UwpUi~E91*)43?k14#J4^R!O>0"
    "~(Mr^<(O@~!RxhYXIofyCn6xg4Ti5~{TI0id)R7Js7q_1Xn6K?M8Qk_h`UH!Xx3`DNpyoo<bVs+Am@ZVM1l)MkQp"
    ")P=M-XkCA6y^A{kfT}Y7Rky%Ucj)C$X9<t-BaF*PFad#DMDx{2d23rsgk|1GY|cwOW*z)g87yun7>0N5Q~yUgc*b"
    "D1^kOXJHWRn>=NnR>%eqLt_{x5JsS1H!TX{-{=JId9>JN5?eww=A-Gg>rjL5rB%Ee9DaF5pOS)Rq%MCMi&$SaC$G"
    "rFG;recIwxok5sq9FBMX7|yCw~YWHD?>ei1C3+1tKgGdv=A|=_?%uBiPdg%!pa?;I9P`=K0+^&R!3YL(4z5Zo1b0"
    "$EZS3><zl-qL|%emP_>|9HuryuJ7pbxFY^CkCnMT=z_3j)c3U6BZKq#eCDifB5{kUS=Zqtzp7Q#&2&i5N!P<8{26"
    "s;cD-wQlmo5;Ub^lztaU<(Gi=9W62sM=qhtcVk>I=3#Y&nzynOZv8{Thxl5X!Urq`jLc<+dCs_5oo-~J3VM*IkC3"
    "yQCPG}F{LX*TjU@a5%1rn<ZvX;|KqxrNKSGh3JUi2@xZ4O-ftaa!u5qA!Wjb0HekF>8o~Vo(LLb{R}Vg-O*H5oqB"
    "5b&FIPNokrim8RsIib{*wd@8S9qrkbti)>ORn5yP-^7$9))>M6@xt1O?n)tQDdX|5#Pe5oQ9&ry38%Rb>v1GM+`P"
    "UW)TRF*L97o6`^-M1<p^PsOlfCHAl6bh$t}GhF5QjW6egA75PlYm3<Ot9S;>gC~`&g2Iq#5eIvlt1>0CiK7K|-}U"
    "Do4o%fVX*!6Y(nFAoz>`yJjkxayWXKN6T~hM>4+Z^4sOZ+%NaD6jCK@l9`7d(dp$ga%eN|qIu1|cD9-uik5S9HM5"
    "Lxj)jrr(l9O~q-37V3Zb<7m)x%Bum3o7jKuZgVm7N6qfp5bmc;0|A4U{lz0w*ttJhfAN$9*vRaa<lGr;J&i7s5ND"
    "|NlOgSN-kTJWB{o}r5dfV7fOiZ#QW*%e$cNqmU|jcXbnd|WZvM&&_nt#*)fbC=vuqxb7HUE?^n);vz^-Itcw1G?H"
    "rE96tqxR>Nyw<D8b;;Opc$GLV5Ep&Dr8C_|EXgCj$p1gT;{HpiU;nA<YWgUkza>W%17bYx+&MK)wryc;<UiBuEy+"
    "HJxxNwgB`v{!>M1)b>!N^2=g8CH~YG8F`*Wp)ODA4efm2!WY(*<Ti_zc7IQX+dM;`PL3-D~b)xU7dNN84pDN3+NE"
    "jfjqM%$-bA2J85#OIdT68-hzoY0c6Ye=o(5+H2NMe-^!1jdm=l^{0sDa^tH7S)+LMn@Irf?r;Tmq3(+}@$CHYjmq"
    "GnnrJ<k$LR?ja;_JW%Yvt>gIIGtCx@}RBNiuhQOlSc4Kjt-+3-cT&`ScYJb5x|rO3<W25UY*F&i0cW=mJb^~Zx6&"
    "@)D@3IoXsixp~am58f7-jt8yRo&9Odc{PCXNK+y3fkQNTR82jrFHnAmr6SmCx9y$nrvg*{c^@Yw62PyKu^aaYw$o"
    "<E2YtJT&?_^KtT~~IP=IQ(Te_2LUm~AVe@*F_Tjr9R07j_-RhM&?o~7Qm#j%Nh3qx^KAA+_=Vb!lbBkpy%TZ!gSE"
    "1>3gB=gQpx=w3T**TLsc$CQ?4vt!saDaA&F|WV3Maz!YiM&Gf)vz9Ul%px#xmkz2NqV$7PAlVG?QKMnK0C>?c5rV"
    "8F{~L*%b~s%i2Jb3rgb?&IUJv_|b)xbIT4821cXYuApM_jU-q_6GK_7{eM2~y{jvKwBUTyaRLZVSC7<((c^2&olv"
    "mF>j~<wRQX|<@ewdANLG2)N(oOrDDBN(i&X!urq!U(@O2X5(}6b%3Gv0x(?~z@;GFoBZl-1?p;Z(TGkpRl^x<Mta"
    "R*j*R{eTQE*~zw@a?wxR*a+W`<<)$dfDZ<wRq-*$y}X6&37~={SPM-xGe)e`@KHvEo?VM#_Fy;%(mU2l)c8y<J`U"
    "3VmM4b0s?EQvUrx}neFre%EGfaDn#CJFh{h!m|(G}AWfm9w4br+Lcf0xs5WgWr_Lr=RS8cLDwB>(a^y)W$w3U5*}"
    "tM<@q>1WDr{A*z8Hvs?7Rg~b+e36H~-TDX!C3e8C>cm*{VOc3`~x!zNSH^B(PX4-UaF|1ps{kqz?)o&E78>60g(H"
    "C5wn-%R`^?fKd!!TqP<L=W~tfVloo;;lFH8M5)5zLE4P~{@+e9EoZIWDt`sfHyfD0q4;hazk%1j?>1Y|=Vpt)v|b"
    "k-TLqGd;t&`M&8lI{S0P%HSKH-(O0w?e(h=?n@n!jwJV~hv(5V?a=V9{?#g~U?sPeGgv1=c(U}k1BJQ1dQJ<d{%M"
    "<G$6#Hw}N0PlW`#v!tD4A5<r(y*C5NS-}~6bfbRLP>aPN5S!9E-^}j*s<~NW>|Yoin|e$M&^lPjc>Q4jIOq^)pBe"
    "4(Xm0hRSs~wT~!}aaU)_Un~}Sw4A9V1>Z(70x5!{#sLvyILXyz#t)ArZi;O3Vp0ZT6PU~XYY-?s~+WBM={+BBq&}"
    "NyvtGFHhcK$tDZWogJ4}V}lov-wR@@`xyadb&V1f?%Te4Gx4x@dX<{DmzP`cmWTiYnfwkpIFLnpO0CV^uCOlByT;"
    "@KY}SPVk}llrr%*f)A_Y;8#h&A1@2PlSooD7t0HISLEbhDKGy+a`TJz7?EhHow6!Hzm1kEIzS+)SG;GC@U`$I7L_"
    "FXjk5g8OLF(GoaDbM(f>-gsgzUSS<0xF$qLIE_+lk+mG*xr6YpRF)sva5v|g{Y9eB#6!6vYgK(roAvsH<35`D|m`"
    "_(eRa+Ae6S(a^Pv^25#>SaEcDh><gj?>@YzI~0TWhn(PjSET-LZsPMxv+oml3XR<%w`Hr{_Kq`TVVMv7B7uI0X*}"
    "(Il<}(Zx}&qxxyOI723z52$@F{X=W8R*x8a>%1sRZt6rvMFtrJ)j*(aF_TBFl($A~UoCNefQ=Et{hBZXQ>hi)MtM"
    "AB?j68?GpZ{`l`uhBzy|eR^cV#GMxy^H3xc_2^WaT@c@4?aG+as9AI_A@_uqVqi!n>KGDt)y`o;G){@i^Pp`j+<W"
    "v2f`6FjR(1EA}E!w`ABeRPusMD`J)LgD-HW0z;OFE)Ph{Wuqqv9xK|4my9JrE2Qs`gkG#iA={s-<z8%LsaCKp>V{"
    "Su3lII8@;LPtlDmy_r&Q2iC*A#KrNg5kjHa2Hi+{V!fpN8os|d0sQD|k|nCe@f37}k!yL5XLsB}uIJ}g<NhH~O(>"
    "6lsBMM(w;9$5KD#ZYiNUrG#O&LVKBoQ9r&t4;M*At>eZD|md>*jJHY9af-Pm&R3{A~($>DbB3L`E^;vTuDmPw2D5"
    "aT{jd_wkEFCZ2J=>nes(@$Kyozx!~skvioIjx$CRWAA!lJBnqX>ghv~E%rFovCM4QP-2n*>&-+*zruvKMI-WloNc"
    "mL5&chXf&94RSx;kK|oq+(mZY>nAKCmRyQ%dz6-2&VSv52oGyFuoUypYPpx&i)+;E#h8Ds~HJ?-;1rU2YWF%Kq{T"
    "W>#Fa*WpzBT6Gzo%WDi_tU{4z?NO0ezd=BUHJDF+H0uod3O9N;!sy=Kkd;dJ=KfRp0tRSfX38-Sa%Lc)l$qLh$l;"
    "$>uk!2bkq7g+2`QW4cWM;;8d=APNn6)b%|H$fA3x?!B?^<#ok{@7i5t7m5lNPMt`)QX(TUM)+17`~&dptlugu>(I"
    ">{>ATysUnZv4Fk#~k>!<nOJjQiDE9)~?E&_xbAzM{x!W116O)7Eo`r>OWd9eT%_XfsYNne75}L|A*)3SJ{tNB{@F"
    "<gqhuhNYVSiJ5m+w0i7P_Q)KRzib237C6;%$VTu!hND}pmG`EH)9N%)4EZ@m~t1Zs(T{4GL!6@n|9wZc?5EvPVhQ"
    "NLh{zlwGxrc_yM@rK%8Z1Uq>a4_*ay5TIaja4W8I;Ep`pdL=J<12FtuiXIorTTStGg5K`11$ubX4V{AVlv%gbYOA"
    "qZHN{C@0Mzybdw`LiWZ?who(u_;byi1yrFtcPQkljbGZSkO8izDm6JSe98qBu98!!RSHw|qyy!y$K4p-dXMAN*kE"
    "0Jo`3XFDiAp?e>%m1Lyyo)NGQ{a-;sO(Uy%&D%xe)ZWirryhUmAvm}2U$aD+)y;MU?|8o>1@bJFX6sp3U;{zUY&a"
    "*CpvMeJFq)k)Ym8ADh0skutgUNa=$?U&7>xP>)ce>|}3mUbTQjwKZyQJS%N?;;ag;<?3+l!<WI#Y;k*s+zejp<ef"
    "eElt@OMiN9dh%XCN0UK}Bk|~WLgf&g!PIcq+w?Wo9o+R0gcsqNP6*s`6=N;#=gX(sfe4w{jSBBLvA+G<_9S`Fy7W"
    "g7S>hZkGJKN*|=69a%bta()6?>Jhz09X8*6W4%)V@pAy|Q%4gIMlIlkb<xl0?}D(^)q^N2!O+|1<(A^X&-5?akIo"
    "wmEV7ROgUa;B_EW#ThhocJi)<SX4RACOWRbk>+>ZOazK-b_K<;G^Z}BbmhCQ=GQ%>pwNXAPNZI!XMkG8r@)w(>d@"
    "~V^fS=mWAYaGQa(aFl>l+}?F?Q2sBmqN7y9(Om+5^#y;ZFa|B(0`{J%jfZSC!Ol)~l46@guKr_7i=4Gj&!f(~@ne"
    "F48m$L~DhhOPq>4=OIrG^ifx@)=O91i6%rLrKqBenH&i7KqL;v37RjtV9_ySU*zYNsT%E5nat^;cY*jk*8sP4Z<P"
    "3oun$Yzgxef5p35#W77*`Kl-M-n<FEdI}_fre|Mmcpy+y*6ID+Du<fi#cI`mk8n6m)3OXQUeyXlyu5l=KMjntjnm"
    ";6wI4lalM3t!2P(^)KG0;Fhaj2rBQ7dt7@FN@Qio5Me_)<;np+VE+H2ip|TG#a$cnE-eLk_{Hp^=L`IvYnBMtXcr"
    "Q2Qa{%;FE}d!^ud$S@-BFh}DEKLiWvPOgKMR80X8a`XN#1P@JfFY!%Bi8%_5S@0+LtcNn<h-(ac2f{{_H9!=6Y&f"
    "(CH`S0}wV+&vB0x(wx=?z^1(!@8ZTo}21=^8)dUKa0C`MalqL4eqioGZ{AXA+VN!1{b7v(C+rgtXhg8c5R&MK*-n"
    "O<fm*jH|JvkzSHymj9w>%^$m<aX2ET%#Y8L=-w&+RwdrBLq7qaaOt$LQZMKoZfW^=kcf_QnO*rB)RuqZ%;**3O(w"
    "2R8E)0j{J*Z36)a+=;g?@qOr8~eWzg?*|mMW)w;j;g|QpqMmSbkGA1o$ED2s;1>K8g#6lI&56--G`7HP$*xg<acY"
    "IAxb*&vD&N{e_DNkpK*ZKpfYaUWowo5AsMgEDX&P(uuX+@@_7{^|hD7Xm=5bXzqT@`HmnkkavcM5^=rs!y*VRUo1"
    ")vCS?<;>z|?$(91rjny6q3X#1sa_??O`?Y1daj9XnIDNpQNV#7zj=*C#9nz1#Y8?>GwJQmuTOvTv~_lr)!|)Nr--"
    "oH1X2Qwf@ibsY6ntPNoT~tTnjz@&?<JY%6?u*e(0R?qG&8nq#Uw-G>PMgE>qpi4^4v`wV-@y130b@h*S%e|Guh_K"
    "zO#x-tGIpyIKYPiAsl-0w6LZl()6n2+H^#PI{^mHWX7J3i>-a`%<_M4fI-}A5T+suTK~7FfV286QgWL3z7^s6#8^"
    "MEtFm^td4@KaF|)&8NDJ7?IEf(v2^rwS&9dlQCHTd74;V@Wt&;99>Sh29g`<FrdVXuF4b&(G%BlS@t9oICZ(Qx_<"
    "orbR3VgXdPBGUbPX+REc`0&&P%RFXeCw0-UC*RDRspsiYxDtJ*<}#ymm=*${;p^4?dqZayuaqJ&S|)6L&=*dO0HP"
    "1l!)mLs-~NkNpNax%R`?)CK!$mVlLcy~RZMsgm6_sFdG3F&XAsmg?A}T#?|bCAu`IJ~xvBd7KpsX6VQ_$<8b$LC)"
    "(?bH08-_Sx2cb6OT<<sa^{!g#B3q-!|hv;@<;CRH7zd>Qju^^6E{I^Adidd>6#xQla6IHd9m=)yc5Pc2Ksz(#A<j"
    "q4s;8-I^xK=@Ky0}Tu<+x8-xec-IGNDpGl=v{av5v17*0H7C55T8H1=qHmG+Df=V)-%1&b~z06pMt(;^KLrXkg_<"
    "Ovz%tfbz~%M#o0Wap2dUiK`U=zSFSiymI0+zdYR`5&yAX-G*q7MkyP<ep6LdzbL(Q90LjL9P*Z(HJ_I&x7sO}xTZ"
    "SB+F(&y{e?u+;%5IF*UnwyF>T*nICl526<h_{n%HOttR#iJ^2Tqy&z+_<`$u5h&9nJ=ti1$i+Rp&*k3Jd*1%t5f5"
    "h=O5thH_l2za^_IU~ljGyr|p1LStG#BM#SYv7T;CByWy;`Rt`IGo+p3R59#nrjUF|k40Kgat>TdBMPtxX>M`Lbn$"
    "4AuGyakt??L&Y#>Hm|LifdY3=&mUv@iKuNvk15zY}ETY$}kt9Zxg&{WjvTZAxxy9$2_zKXNYt)XdT+;V(l06~FJQ"
    "06N0-<Y0D-FD7~<$AKLo1yD<o?e2zxmW5(V0LodQ>D`6oSf$?bw(l&VpqUNqyttbH3%n-;1)&l)%sBos49ud?<0~"
    "pSM}IYMOC<lc)6F&*Yy#?{{k(5%O{_|!J5C><2V4#@#tsaxQATn1Pk)<XQJ^1@QO)eME*eUPTsse`sZp6KJCpd^z"
    "Uf|Mo?CF3v=;YPL6(g{pMBg`0XFLa{7II*9ll_G0{0D;=2YvtI9Ni*(Kt;&&)4Dg7`nre>r)}JpdPepR>hi_5{X#"
    "o{X4@Z0JJK`*{IVJ4ub5jzF3VH%U><o<M%phh4doMy&bEah3!Ev{VVUGQR>zdx*%~u)t6!R3_P}S^IN{90uXAhgH"
    "p`X^57lhL)Ot0W$?dF@c2vDd5f;^KJSzzCBg7?LK4J!s<!(AU|7j$ia-E<3%>t-kySP1_0!lyAfPX;ipuU<`UZ<r"
    "B8z0+>mk$c4?tr4{Le%dNgBmf|T2CF~#)FR5|m?d6lti89q1GkLpKNq-cJFIeYQWJM~`q6*C9d@%(olM6(Bu?!cU"
    "gXAVuS_fey93YC7~+DVb39#@qocU|>u-MB~6tY*c=0G3rcYAhb#v5J^|GI=wepbX+oi=t=3#-WKT+NWc&8gU;qDq"
    "j60>-E#Qmf!CS3H<>(&i$WaomSQq0EhR1B(37-L`t9$EjE9t8s59<B-zh0cX~88O!JHy^{nCeSmxQs(95hFRiB-Y"
    "x|`LGeoD#4Jr<&vfHR%~eU5W#QB)?HPJo8*n@zk8-%k}ViIIq6#bA=;6HnCyiW<@1-~Rgc<j=QC_eef;cPqFNYE7"
    "MZ-90QI(5v3W)cc5%jABm&2^*A`ra2!^b+u7$S&}#L6QVa<4niCM)!-6Y;@Jm}jh(g)UwU7(Tdo>RRSWY@&Ppj|("
    "4oy%H5HPuL=Y=bp-v@=(A+Qb1B=c0V2XK?vpI!4zMrJG6C@Zw1!Ail^k9_8wfR9CUL0g%BqIXO**Mq>C;1aBaAV9"
    "&fx|C}AC&qtABw)&zzJ}Ac**Hx3YSF4-Bd>d5VwF}^f+yY`_`8nNnZjpa1k>$X|5_4Jk{pF<(AE{m0)Uvw3bP6z-"
    "uVb4sr#WAropRXj_Tq4rI7^>(GM7bMe+;;9Uh(pXck%bB5b6j>mm5xtgXNRmhot9dji;)#L@ok4kN&&+A%O>!XgP"
    "7INar>?XKSbwAZoR8}!Uoy~5_hA2q$tl&TxE!>=p8?M6?k(mqtCt8eRuer&qE6-hueQ#yXzE@?&G*9DUGRpvv7jZ"
    "Z8nmAC03ykror+NL|?Sdu3bx@X-MvB7D6X4wofMj@l=`YCm)Ycjl{UsT29V6I~_;EM+uEC{a)clB~#4ZbqHE-ziW"
    "=Z-|?!QPle|mFr^lQ<PG)KKuq@GQjx)0H^)!i^{I$?JWMT_QVEks6H%_!O@xAdIFcMT@+-elH`5Tn@JcBNUj@dZ9"
    "4k28|Sxp3F~MjY~)uRb_9SYod?Ad=Eu;92zXL=Bl9xN~3(>K?a9Uzvo5;A_)Kv3eH1TT$U6^Ee<@U0A0Su1cI|as"
    "|thbt2pO_FU@N;0Ylhl4#{Q3aTaXe!=;d-Dr%W%b_o{h_r4(9_VjQ;Y(3EIl+LRRah;YAo60rRkpOqBQHLKN%yF{"
    "IhBFhtasMUou^N@Dm_$1dL9o@ls8uVN!N*n^yY;z#gvM6D?wn%_bXI<szTo$7&S}5c>D^?;ydJwWP0e}WH3>{Rfi"
    "qKphexELsop2mUxi;Q0h6hio@I|m`g`orns6R(g3+74K)S5UZq;RFZC33Jc!#nCEf`|=iYXEMJGR0@bHXXs&#t!G"
    "a>?G^YWP!yOtHw{e3G=E5(Q-l@Fs^m15d^Yjd(*G~un2WM;eVyHX{YW_Eq&?7yg<hMZ+bHCVz%8gk1QPG~HGZrRJ"
    "C^jlifcgcITqz%c)RhpDcprU-fO2}S6oAT9vG@)^sm|g+{t8<$z08W&=KQ^#x_X`O#4L%_Xd7ebiukPh<c5{Q@-k"
    "@JZD$<SMmUyxllkK;*6w7=bJGuGA*Z~~awj|VC-C={I<5@a_FGhD<>~lqex?&n!GiX-!u@G=m6q~t7(6^Y+d?QyB"
    "KP;s=c9H9c$~ut-I&gl;d`df#?H6i6=7Xz>zQoC7X=i2qd{<b8G`MA2XIAVwkeQo8N8z|1g&pogd-MShAmHmskX{"
    "y>VRq0^pZiiJZu;X*BRdB&cUYbR`CH+M+P+(lqFvNu=aw4((>#0qk6!^%)V=L}`?OUrja-E<?8MR=_8?2o+hmLWu"
    "20}1w>(@?M#$Dq*=d_jEF9FURlkgqSM*|M#hj}`Dx&+Myk=8?k|=uWePt!s--2^Yi^STa0JR|*CrUy!V{Q#Y+7^e"
    "v+D+oy+!E6)SY>B-y>Ok>78>}%4`DJwl;2|u$_h3ry;8+ZuamlR8Gv;4YQ8u)5Rz>O4&}7N#B+LYNV`=UD8?T-+1"
    "FLS%c{}xELNN{7j)|Szb{FaEJM<#OL8Rp+N_Wwxjg-XCVOHq)^VZo-b~0q4nWm6?W+x>u5^VCioJ4H)XG)+-4}z7"
    "K9}I|iyl@SCb+igPIYijZthjwr%9Lc?2d+wxHKjwEG9QrdX_xb52853#>||2zJM~-3Tr&*)T<R74~&z<oPhqVD%O"
    "%#$%t?+KX~4g-@Tc}yF^MLNru8PolRINJr7>a-BxP}11CAwUH8jUtCLO~t{uiDld=&xDY559+$B7@ukJ1rXTb8r>"
    "8eJz8J%4k-J^W`^QNuxNZTHvwX8QLhtZ{hHNNS~?3GhEqX;|GJVzU%*Qst$633Z2QJk3@!<iK$I5P$jwVND8`X3A"
    "6bhk&5#U9a;O#8V<vK4I?EGH2K8+0A(Ad@sq&4OgkJ0{th0Wg{^2^P_vaYzZiZ53XYbhWL*5bV5XRo|-gN@Y1DvO"
    "&r&U!|D$(D0g%V3THJOsg|b20?$3B@>KL0;2X3DHxWnu5_Po1Z8RSFP|xH^IV*G1FG<WTigWN6d)-JrZ?om3&PMy"
    "2d$!)a<G^pE5w<hn_isnkB<u%BfgIpWz({~I!i@u9d;gQr@hj)i;3iz`8RrvE^Q91*NEbT#M>bd7l}Bk`bZsvX4Z"
    "j=&niBUqf&CyvlW#Aem@x_EE3gb2Cb;C-p6vZif&ebRC($>kh#e(u^<<gpk%(i9YG6z*Nt$p;36|U!(WI)aPd<oD"
    "A&KY1)WqLu<PSZj1b;xq@UZMc?He+$GKA=TH%Cx*_R4ED8IK7PdwGEK}yvLsxGLY)#YW;ONV2F)X3!c*~OR{Z!_P"
    "fzxD*<01ya|*C22Rq(lZofWkB4*%!SmNsF9cQpJJ?5}(g%4)hnt&8RSX`@>j~<f(8?G*<I`8e0CUR~F@1q3Yhc6+"
    "Fc5Sy{!yY_m#Huca}z6bFT}s)~tf9*RfdJ9<-#V!limGT-Y(=>YD7`DrtZqMq_XtXaC*09}*2@AA}ZWnbi~*cG~7"
    "+DMq3Wv$5H(Kk!<;zw0Ee@Oq}r)Ind{%rC(tpH+loi^SzxM8kN(C_3=nrgwJ{mVr^AAFJMXSE@`rAD8|)8_a+bV~"
    "`-yRCE&Yv%B@Ggcx8G^JkpzDo}9X5#Mfu4Z<m*In=>6>n-gzs9<i*+JH?D9NrS<kV#MOy#qqB;#lSS38}(n4xlO9"
    "B<@N+S$g3Her7Zn<N$ynZlcR9R7i>%Isy$X%K7&Yq8&}H<V5H2+#-<;mc<Sn^Au&+TPlY2D=CSo!x`&I3D!3!YGX"
    "U(f;P%UTe5>u({LHT^MsRI5N$(QrrTDbK1!k(DizL!$Uf&9s%y1#4~`i)+Pa~@lj60FQ4u0?#J8lV1G9Zhr9jZ-f"
    "q}F*xC)Z<KY%Q9SpaJ?d{fHw0{ss?SAWEb9?__bANBJJ!lQ1aC_70n5$iI#|HK$s8f=7@ISf%3rrpBTT*fsJ|!Tw"
    "8*+&(IG0^(BW7t|MmAzk8|?ku(16RK2Mrx#S`jC@Zdl&>VWoKx>C&v?r0tc@BqvQnD#9-PR`f$EpwbHUYlvC~dJ}"
    "Uq^p}D7(oa94OYjQ!{Zei`oxld=DA>S<b?j-*HLvNKOSetD$oSHBD&(esUoRcMLe-V!&dn5<lF6}S$fa$Ey+nefK"
    "(4#1b5Y|9720)aC>zP9)wyJNx*nx{5VD9!YRrty`3V3hk_O;)xFO+x(}Ukg8FVR-*-?(rG^pCM{MV_HY1MK~(~w>"
    "EM|G+A1LFfLm$;drn@OcVJvaZOx>%Nq`*Q8H+n0s#8P^OU?1E&~#`&6IQcm_WYwN5GXebL;1hN_*y3wqtIj?(jaR"
    "0d5QadBDC;8M+0Jxltiy;;`#1eEYho&=!j4$Y;1u#Cnd76$g{CQR5$7jEsyrbVbpBX>b8UCp)CNe`9ou!lO4XyXQ"
    "%(I%opV17^tZ1(;oz!Od0R8<gk*NBv6aLrix3h=gMVAwnW~|sHJ(Nx>c*)WxCs}|WDP5#1?iE+u<CkVb?w&A(=Ds"
    "y{f+sOZs8f1o5eTHEs3GX(1r<AX{Gl^9cs)cqqng}%JDb7APgdw^ZY13^dtw~~5~w!-hJn~hGIS4*Kg5%b`Jx|CZ"
    "^7+NJkdp7(D@BoWy!~8aCQ@8c`M2z&g?m2rVO6KpumU*^P6zaoiyDo8HE!aI0lDHTn@%$ClM?AvpL3X@j|f7424Z"
    "x!w59HCK*L-6_}>z#IvDLhGtTVou+w=!}nr3)ylHjViX6tGs{cTq<=uAUNV;ph8xn}+i7iZ9Vc2$gAi`0)n4}ENL"
    "Myg%)=2SWy&WvPeE?|z_rZgxUtA4H-mQ|pC<#{>tt{fjKVt-p)ny$#%A4Qf=qI77{E;);XJWA3}&vyEko!0iLk`x"
    "`gkX3QE_C?lJkojM}YN$RQ&e4yZKFO#<gLr92{yAj$Y>cb8z;5-T+0UDu%FklN9)tM8{sw0u}j>9*m?n6x9Hn4C@"
    "NCaIfIf&tPt?$zX0(F_`UkJ382mTf6aKZ#X<?Z@2gMclP@It#*HZuif5n?X>p#!~ORDPPi9u54LtT_qPwi{?6W@-"
    "S6-8w@MjIfax?trRk4dak_5$oH)yvO!M=WpTXSRequ167|bUI^NGRyk209uwb;uogS|A9ekcekX5Qe$8%Ev@H}M8"
    "@n-oq%A>Yhz8j#NR6~)tbxjoJolihG@o<yzQ;FpxEH)nLKxL;q>oFkV0#FE5K8WMxUuO!J1_2{n~TfxNwQk?>4ia"
    "uz>na-N525QitMu~2IX_lqbjIG%qe?afuEa%+FSMczQ@xq=&>pONL4!bsb+j?p457EZoPF@|q>HU28+NyuN4oB^o"
    "Q0t3M$YIQLkH5UWt7L~kMitE+61E%8k$hpwfGm}Q<?vJzC}z-6`aT%W;&=%!j-0i0C8n5}<~OklucR4*R%&a2D^8"
    "~wvbO(@XDRaL2^muI(q(~SZ-jM5cK$<(b?MkzLlqf-N2jz5fE5#zCHiboB4<ZlA#suw%=YPG65OSWS%AqLs0i;Jp"
    "$TD)Z&Thw=?ON9IPj2tDL3$0kfW6*^q|X9ibWmoi!u{aR<7F^rId^}D*J9(>}@ZLoy`U>95(AkA*opvv%SB)AMb>"
    "NaCoq_yF0-DH{3lqh<2mRy@OWR-rC&`hpl#dYiqZ4u)j0h+uR*)?+?S>&CQ+m{$Tr{l-WkiWT$=pU%}zqS9nYyTy"
    "@(-EiWBQt2AxY8)Zzmr`vUUQV8v!^~9(@G3rl@`V*u6pJddRTt1bNN2dVg1ThW6yD1};aGp5ES|TY`Rk=3xzyv0P"
    "4}Q_kHO%XDmzTbCJKWSArngzwNk3zDT+T~l`sMt?9`B;4hQrBSZAR=mC#ykjz1wwG$lk={@5kO$mz<^~i9bj;7oX"
    "mDW*6_-@Ay6EPJri#XY`8n0Q8G(w>0s4yZ@^%#&VZ!#OLUtEBahfAuXPDS?(Xi1hT(iHgST$D`}6oST@C55}S(ev"
    "jyh&Lc^{B(Mwq0Bc1R_vW1K0nb`_6gEO26@rQWWn9v#XJOVvJUOAb+gljh=?wlujOFriuuoI;*dl<1+mSaRi)cpe"
    "K3a~85^&*MF!dxA#GEbBj3eaS_B!-ygc^1)jk(zmtQPLL<Y7*9^8N6n6aVIKg*hd&2usOC)vUEfN!lZg8mNle;<K"
    "HKDyYroKw`fF(k$r$gHkHYx-b^ysPkbRlOuf`&0XjglLW!fo!R`}#`ox|-v8PY$>G#8)V#3h4M;NieQa)zvmES6-"
    "I&gYjx(+Ycc>vMpJROrm0=_gos-J5o1WbP*5C;GMa`J(F?dV-wKLuU@7#BL!j9wj)ZB=sfj(|9-mI`5aFBs%_s^a"
    "60j3l*sF4tVG3XgA!&+Nr1cGj3=Lr<)MyvG9Cb~!>epierVoXgrlT5#Wxd7-Wun1HTx#728&G?kXCt1@c(IQE|~h"
    "g=}stdJ$QXQOzX?%dCj1A!VP*9pcLD<-H%HCZNe?FK?i)UOGt076ldr391kjONT=U75OZ1t`#&`s9nT)m5wc9M*b"
    "CzbmrWfV$ANf!MPMZ6>6Dh5NUFjR_VL9qx^pWW#;}Bqc$WC$Ny?@J_3jM|YYB$D0b*7eApylPhSM8Pt*8W>1A1Ed"
    "2@G9kxye$sBseS|O^sufS+CIHnE2Io;(9H4(MEWORp}BFG<tHd3L9{0lCaMNRTLjjSR@psixSkE4XS??F0ENW=ij"
    "f*NqT(xh)rK~PaEoLnniv)t}LE-P!MQP+N_oNLJcDfb9bv(A{^22`UG$zLZ}#fHQDzf;b9cV*7pttV0K<FUIJ?+y"
    "0154NJc;pTRKYkzAuYPG|y&HbJB?!jO)+>F~>gDv3Hfr*M++k4Ue9`MEc`<n+*dr-=lBlKg&_9omOBI%T*9T^Go1"
    "JBVt5rY!u96O;(sD3ApttaOEi8+5_&Yzg`Z;m-HE9pa3e0-HmtWqYlNNO`n)3LDR#o8lMdPFLZ6l#K8(310l9mvV"
    "GTWwP}OwX97o$)~YOSMJ}d#Ouv;3HL=<5KEzlzpPGJu#x!vvfhuB>bV~D_yqu{vKf=iL$QBSZ8K}ZWMBWlyb*3U="
    "QA)A1e)o@x0J6Yo39LqwGBDI(L@Bx}8qSM$2>oZHWG2jIzD3f`5gzFns$ErnxXiyK;>7at`|Pa<SQJ9{@{C)Gv(C"
    "tq0gTfkI}|!kkkQHtvRE@QF#-Kwy*Gjuodzizv=kV4G<zn2aqRfmlfT@qR3<Ayz%ff{Y@51I4ZcuU`RA{TDkhDCM"
    "sBTJTH|vY7`*tv0mNk^ejxcCg467;X!wYY5E1OV&NJQdxUko5lM8@y!|dl)p6l!QdPKSU$u?8Y}cN!Acw}cv53B#"
    "egrb@YM8#oHQ2rdrqOV5u;XE&SJu9Y_bt#%(WwjjIuDY?{_aT8_x~v@Y(IWAFGO;-z{go_W+$YiER~p^>BNCus4k"
    "QTbpsey*=EIws#Jqt>JM0V7Rjf9AZC?+FQH3z-w;};&>444)<HTd+nW_&G!CQ+zLziYP99_xatFC>$%Jykq96B7@"
    "#(MI)!ciF=*F=A9OpnngVNBN?7j|##y~zh08W~+fOX}6U+X@vOlrx->^R2ytt}13?d=a%1(449ntZ+ZXD%0-@Moj"
    "CZR8swrSI>**UU%f&8kJpJ`0e+irX7pk8;gGH=(fN?Bmavpc2CcI@EY;jSC{CH?*)>~F)R7RyJ_<i;7{Uui%4nhd"
    "tRZEl98ww2nZRrM?XVHdYHw!VycUdEuWGsntbtIct{n!!H|h(*2yX(1TQV)BL19@U%#ipu98#|wOG7zOE&oTIte)"
    "tujwWhz^Y(G$cH8MNDq^5|Z|_5XzYso145(reF|7oSPW*N<`sw_DBNM6tsej)EQ`FgFo!7>)C#VV`Uj5*ZHOkJ9U"
    "x%*rd*70R$f<+#|HWQ0o`Czw7gNGkQ?@5qmYc|5{0R2LOQ1y}_-odDk(MjvqLsP1kCN9ouqPNXY02k{gHmWWmAC{"
    "K;>wL&x`h1`*c3yUSV_pm85+H(x={C<71_aDH)OXAZC9zNVT=nul}y{%|-c+lF94>pJ4;NW0qZ)c}9M8}o=-7wlg"
    ")%Yf6+t}aR+1+l#kDbl_=D{!wtDIK276nJiOfi3$jv_(M+IZ{aV3Y=7BuD;tfU!xf!nviYWuA}Y;E64NV#}Y{@+Y"
    "?ZKgpKM6jmO%FfR1LaBM9GA5)D{0ZD41pxh`Ah1;;*D14e{xu-N;@Pu>F2JbMT0(pp13{=N%ONw%Ky6!Fo02|3S4"
    "2s|ah0gHn@Wka|kTjj1fCMY)`B}qHUOK4O5gy(lP4ue$<(O}GuFCbpVor-miJkgi_Ou_W1^3KlZYMPMO~uLix!P3"
    "9(u-utcrk)gkJCjacN)vV-QK{KBTfS7L%(ByMqtQLSxy&XWls4l`KZg{VA^^Gg|we4Q{@mt1krcmwja;Xu^bx$Pe"
    "GN`Bz!T?fR_7<2#^Ocu%a+C!e!0in4TgxauXt3oKf^4b33?hWT+`5GfLU(1aUR`XlKEAF=zJ|=B()+WVGLvQH~^t"
    "<i6kWN5Fl0FNw<rsRSW`X2Uzcej=DQWup9EbWRfbLb-!0mvzD4z$?=!z$efXCKkCSsRk+V_sUrxd|#Zk%8S~~OBc"
    "~>OrlvRop@;!Po&87dKo`m+WlgYL{0q9c8yZuu04pthg(kpkx#7n6D$72iht7@a{KbhHX=ByB<Pf%e}(KPMlRhKD"
    "mgD6z1S6t>D9$6e8SaStl{{wQQlfz*QFsj+^M{ag6GGOGi<=@@|_jf)3kvb095*g3Q9+U&hH8i0Z0g@4M5QgvAbZ"
    "!5vR4iRMlFndW{MIy=8CAT``N^7`c$i56P`^b6H(qt*ED0OT`4hNyIv3LQ6RcQrmE`(Y{iyp@&CD$M4RMUx}B{#I"
    "1?kHK^;-D{YtDS$3(b?zD-*%J~a5o`vupb_&J4d#n@j3yY(4fEFn^5tbF@2g`$2p#;N%M1OG;nJz~60w*pKveDF9"
    "&zBP=eKRfiGCAvYO(~bpet-Mx+mk=vI&~!s0DV?wL#f<{hgyEhR<-#!tJ2ROx~R!wG+HHIIYgoFE*HzJx-h}~7PH"
    "-O?i_MAq6O)kJ(6K3SO7aZ!^q<m{J<ov0iC@toepVMLXzEHzaoJXGyW{50VUVLOgqUn*>m!WS}<qikA^^$lu)a4S"
    "_Z#yCQRvsi~fZqO;R<P#VBItYL0%J0oMjrRUNSN1^J+noSPFmF@WI)ZM=Sk)CS1y9GLJsiG&`^jl4Ud&Oih*F6Ia"
    "eBpr{jA61g_;gFLTp|cmoU_`_dk5v2$MR!N+GG>&^QRX?8cJ+bg`-TFu!iX<(VcT$i!-##6wrQ>~@7o)YwEG!p6c"
    "Qlr6w|H(Ma+$0A2gk6^_P=3uT~JXIReFyuty;P(@o4tn^g3OfZZ?W=kN0MsxN3|K|H;Qu{`q#kA8}V!GJ6OoO4vY"
    "+9QsS7m;0rNDdI<bWnDIO4tpuV(R)soB>sf{w!3W36KzE90iLhsQ|dxkU%9dj$9UJMOnYy`kox&q{eMCo~DBvOie"
    "HL<Q_dJli=Yi*35c^@9if$*pu-6Bz!*!-`|USnpA#9qf`zfl%5iiAYY*6u4y<Q?6s?5LUHmAL{P6?wi{8+D&*HT7"
    "~yi13JE%J(8+ilM+w$ts&mdib?yqTOCaI*cdri5j{`fneU^@bv*YuChZi}Gel+TQ?VE^hn>ctcTMXekQfEya;mU%"
    "L5z|gzJC;G&Of81f0mImNAd8-s-bN#Ox+9sA0&CR!dLG+DiRM?cBI?%4j#!rDG#tfD@p`m6PRS%6bF>Yzd0Y&Rs-"
    "Aw9!(ZOn*L2D&uF`86bXWRd)1Pm+g7MEYT6>wNoETv^-UVYVW?XYp0SrSp$wz>@P<YUVFz2c57pJ`ER*E0z1fzJ5"
    "M(mU~NAcialD~;<Tp7z+JOjAi9461Kh6rOAF@tP=dOJZh3V6xn^5J|ls=gja&ERl?DhQCFs92rG6?!ZzO@MqeU_F"
    "e&3ALPrmB=xwCM4%M98LCwBW|d`J4l&EwJ9^)JDG53kkr}~W<81#JFFNlW2`E{g{36x4PiTO*a~M`2I(8w5W>tLs"
    "^Mx_{KhV{JVD7M&<L6fImoedEmCDTg=yVVJkp&AqZwKsF?}queBY}XvE5!hdL8pDs~iJWlEt9a-`w2{+r!~5h!8u"
    "icxS(VaIoFq9}c&-qp%%r4)$BEaJYNWj<%!Ccz1JmE85*U*xujW-#^%DRk`O;@>;1?Nc({6M=n$GX(-4yC5uN@ZY"
    "i@Pe~zi0y(gLDN#=NxIi6&WZ!e17M8z6Y==3iQ@#jHrc`RsE)(s~V;$gXuy!_SL*ye4js<UQ%ohIFjE4fG#qFd9Y"
    "vFf=~UOZ_sOGSr|_?(^LoPGIZCZaMELz(6eBZVZL0}iiurJHY1?ZV!mnm@}`gRf2)sRab)-8L57koWZ~PXeiWUX`"
    "qy&qkFUQ#-C|jRCbA@CGz=b}!G&j3Q%I@%HLV;1;408YXnz1dL<C&966n)xy4Tu`vI%9x4`;_O^uWe<z2E)i462y"
    "TspfSa&G7iLmB$ARPm{noW@@BU=f|w2JSZYFQD*0m?qQtXkM%z$Z-{On{N&8K8E0M*KJ>e!?(;;5tne<EN@=-K3~"
    "rCw)0uIgt0}to|7OO@ZHf?wD#8pib2cuwv(vOmXjrXzDP&qTZPAccaP0ih>pe<@#5}!Jp44|CQA{0=C4xtKwf8p2"
    "=X2VwOzUnUu+;Csa}_w^z_wloblgj41|NC4ZH*V5!v1;Ql$|uI#$hFaK`&`OQ*(z66)QAYA@J((vJFR<QP)+u^}}"
    "zaI_<o4fnFdz*u3Yv*7m8f>?BcZRK<&31Hf&~NRw!kvS`=3p<}-|6>v+k^e~ejM#@#r;y&zDCT${05~tRMl)q4Aq"
    "a?1-sPuujEs|8{giO7vB?8|HRZkG4=m>roQ^p=lED%!lT2p<1-jg@})iicbp7|hzHMr-=Pvg7}gHgsEe_;wE<Dy0"
    "fH!vgz!6{d)Mt+0Vz5SD)Y72b5~8O<_^)|M6EUar%}PEDps*KCiYmOTBvhQh8l|B)0Iw-O4Qycb>{TYQz<ulthsa"
    "Zs0vIc(2~Abf5g0pyl;&BmS7&Eul(tk)5RBd(5D+OS-P*O%()^P>oUIFH>09);6YO=O+4#yXbPirikX{+A&4}<1C"
    "nU~Ib)d~n!!+$jJOE6#0YrR5wdXxYl%5rRRULrCghw^R7FkmQeOX5RpeE7NSK@cEDqmi;@BiQ`Qc*1%751Et7?GE"
    "DCWDQe66IygarHm19Y2_{#u=lo-T<7NP>Wq7fm|u!JS0T%U1MboF<US2yF%LP`pq>aIs;jp%&)s^9*?A_;v*)zRG"
    "SzyNI_7g%PF3Hv)WuaEwMS&ioaQ1`D0(OH}YMX_Uxpg+0g#Vjn=ugjzinCdt^YLz!-ADv`0vB;&w$nFvHEiG9D^|"
    "JHX{C4!P+XOnOW(2E(mk-VeZkOImoEj}4xOG-rSJ(U`MV)dU`{U=uczokTkjVZBjSP|JiRZ%Xt!UD6PDk@!v*}!d"
    "+8WT1A{6})hQAH-|Myq16iRV8WoIBmrAD^#NapHHtjK80~@>QBJYD!2Hj#XCzgE8b@qbmY?S#W)!dhVR#t2<%sLR"
    "IC7N2)sES}h74+TKkMDwdIN!9!;E1znzi<Bk%_Y^>H56<wdW7FiGBhb6s>jE(pR(d?U1<O<qXU)qt$H+QehV$Hu8"
    "#*qV@8L;tikEfD(738BO(^4SiMwhHUT}Qf7v$2bCaKr(6QRONO3WJDZl)d`oHjh4iDb`EZ1(rRQ1aHI$^2p@SZ;q"
    "ZP&f<y`^P5?^xW17*x#+c&m+3fs_u8octoIg~Z5DsjB?AfLEo>!MItbV#mIa*QD}t$Gf-XSg$sk8auqkrkIA5^#5"
    "=)1<2!|y<mQ{cbjfqLtunEnD?x0Mj!*L|}HeWALe*OR1dl&X5k}OU5ujJ74JV;bpWtqEaRj<pKDo=sU*rsax1FuL"
    "+DLWh8S}9@NtpEFWu5rsqNjA{aGt2aDVM&pZ5ho%}oa=i?)njiB=%xn1>>_8>H<rPuV0|_#@DL|23Pv>}57vFkR;"
    "1JjMj%$gk&8@{SAtNlXN1x~d?7a>Rue*##@5pHe_y@o!7aTieT1N1=~c<M@<AVzt9Jk4+1BGM@AtCy<NW@^v!|O+"
    "2T!s=em@^Pez5rfw*BD27JPiN^>A=@zx`zJ@T@&}^0-#LB2bVHNLORLBCcBJ3-UAmkUVWBKmM4sH|ta@c`$gc`iM"
    "nG_^xYx*R{UuTHkf8e{r{pWypF6_nF7xYD~zhBB46;5h)-IYWFrX$4<Mw#Jz$1)CsJ4>wb4C5jchhm4^OLf&hjV<"
    "gOZ&!$+#WdL`sc6wu~3lc;HSl?-TiDwNn5pmMq6yKOj-zPY{Z%@1$!;+onSSg8Rsb9n=C{17Ls($27T)F=gYwUE1"
    "$^zvee9Tuf#(Dp%M&Buw{!zhAsH44NbD=?=RL(=oHxB)2CUxvfMF8|196A_DOjvO<D(%LyY0<0)!<^}y3_X9noLH"
    "uyI(VZi8+ftNNd--r^6As+G0utFu!MN3dbJ01V4Mo!9h{YbiDw3$3Vlr&9wYf<zf`KYcRN|M@N<R|?TFJ4xDi9)k"
    "l(A@xDGurtn4!?AV7vc)h1A=Wh(-oc^zvoWDF~tMCz}r*-|r3XZ?&`b)3eRNgUz$E$M+v*{U`9bf7TmpX4&J%+5H"
    "Fovn*?aIQyjEAM_qWgUxoWbh>U@Svo}^=6<Jbud?>C;&eCdcXL_4%G{nj`7YspmvFyJxZfq*e_?NeaC1F<XeL`sQ"
    "?wQ#KS+~{JR1_T36heTD{pZ7_0p2nG~3~auqRu#n!gLql#GH}%EKfuGZW^ak)f9(W)>PTQ!7+UhyAW?yv=_)wKQ-"
    "mqpV0X>}HF8A;3s(Mztfba3$1&bN=w4elrO<9DdBATR(>{slFU}bJfPZ^wsMXXm)Bv@Cy@Ncoc?aAhi+05d$TLdC"
    "V+03mG02*>!qxRWiN}1<qVxi2hlgqn#3Muf;H|auzimvoPll15Xn9xY$lfI4$PR<v@3`VH#PEDAr2$1tFISm<)#5"
    "xhC?KQgMP#Ln}GNymN)Mo#h`Vf-Ix}ITTMrNJm6#GMy*=8N6FJAv}wPIR=7@WWbG<Mchaw3Y-%H=y1>rpGrjdy-="
    "DXZ8HHFVwu4Us?khe5YgdBS^ySX7gQclpqD5&0P%Fm)raIDE@e@67*^*t_&*>|!#GEhHq5v`B2LR}Sl^(rQ(CaIR"
    "(+KoaJ{I=328APfD4~Q&UiMN%;`JKsYs<Z_y@}Q1#-{1)(A@GYYO3yZfPkNV5af8Wce(U$R9p^`0(+=e(!1T$-{^"
    "3-r3**T8cqr$p&Xn`kN2$Z$3W5i2O&rUN3w4@a*BEN1Iy@v$Olz)4|z;hy7ZKoI>w#!8=KV0J2jXevc4<^92YF4Z"
    "6(A+IW1YliCu|Prp}){w_^_m!`i<)Bo!B;*c#He4pTZQ{kfdEwFa9xCB`*{Ne_k_JgNSgJ}G4aB}S8QZyr0GEa|3"
    "!n>s{IPyLI44arS+3<XplQ1ps7ulRPpw0v&wsR@(YkbYrEw65wXg?Gx#4c$wB92$VWwP&$70g&Rhe-XVZzk$T=oO"
    "W@<FxyN5d8RyD{4mVd)JM#H>EMSKyta5akx8QdYH<JHt_Qct}jP<o*>YgaClQ0gUV0fXr|MgBy~EXD1!5TSxd-A8"
    "4`om7lh@gJB>oY9SBei3K6-St>H3Sj*G~{_<y(<Km!i;C>?Z)ZIR)z{hj4hl!!5Pm2g3+xHQZB7EuPZDS-loQH>q"
    "=P6tn?pIzzDkT^1QfyC-}v4{q+JKz(e=`&;*IV%1bgM;$(061^Sp(tlpaJgHc&`Y5C1{b2E=<g-k#PMY|MQVUL)?"
    "awos~oAXC`5dY1#Yy^swWaKGDSCnYHI~Q4m@wxD<p$?Ok^YcBb(A&Q6jwf6C_OuyD6I$6XGNaQ;ID#B&a84%qxrX"
    "uWabYe@@?x;a|8ZLu~fEzW_o_W<P>}jBDQ=W@lyhV;fWk82O!d^uOK7^oqC29P2B>s%UedL7!9~0;uJU#CIO6Ka~"
    "AJ`wSsx9T2A$@Vzl@a7-K@!d?T-6iz4HqZ#XdChiIILwXBB&Qgh#^15ed#hggR6ono!*omN;IFAH~%?qV_qr^mR8"
    "2_-(1ruSN=1enu&*8C~zKsLq>BB(fqDE~O)C2PwuRrr)Qkp-@iv^rc`w^t^%=u_m-hOpu|5jOhiAn-5CAmrj>TVa"
    "?ce~9Nu$svbWT$2e+0J<WZoIp5vh(ur7ij9BsW<59AJKZl%eY~y`;;57_%yLQ*k9J?h}~xME#DB*3T<g){2#3y7L"
    "~_-US?<8B0qvy-tEE(o_D(q#8HAxGQkS<qTe>R9h7y1SwhHQ7$v0-&L)?%#P~0z5b_*A`lc!?R!1f*dF?UmaI%>7"
    "jM9NGZ^D$#yWXlweHuJxV4*v1KQ1Zk127`l6D`)M8(tSJU=46SfOuFgh6Pv<-~O%R4MVl@(`_FUewM+OO@7C#hC*"
    "l?6wODcPUgmJ$w^6?7Gsos?0K>)hC-b`QOj%AQt$?%-}Np&3&poLxBAx`Jzx$S)!vcdM&t8dCyJkGPAi?G%lD&1p"
    "L=8=gGUf&O16gDA``0{gY-2U;|5yQkRm|+4x7O;@nLTv8Rj7N1f$3Q^ERN)G_AI?bX(dCxCv+z9eFQ*!ukSu?U%4"
    "gy4~qj57;zt1X3&S+yiC~6l?~4RrUiZfV%Bv9IMX@%SirHa71+rcIkJrK*b((vjV(#u^s2MvaR6OpY<`G@GUVQ<u"
    "!aFx+u)grredgP$)^4I!K<Vd!pg3!(vX2+~ZA#Wq4|oeQIo`9xYfjKTS50`_2QR8xlzByF0DF!FFuGx%pfqKP2sI"
    "kf-StZ;R7wP(yIv7q*%Qy)32rt%#>XEkPOOF<_J>C=||wDc`fp)2>XH(m-lwYumBCE)_}EXG?0!JM||n#<^3E36j"
    "*uaH9MeF}XGhDl`=3c*+=8bGn~#dNBEXYJuN9(0({?C_*y<o(Y*Ufp7#NCc^KS5YC39VT-?};n5;Z+CI5ifYF=Gx"
    "_Dfwv%GLTU%29CDFG^o)<4g^a2DJE1bvf%=+?Kz??41PXAwjMkee<mXg?Q|a6O|7M+U5t%-JB^Hk{Gn&YLxH1+k6"
    "uLkqqyKy%f_m38NL^182H-q)Zj6&U?9#vq<CmVCI1(q=I(KwHw%4oaCDFD{SHTe<2IFUGRIQ}l_X$-UGh|EgiovF"
    "?2=W)lYb>9~3_{@;h~<fH!$PUl0Ke8l5EDO>V%3kEy#IF2j}7W9Tr@4VhQ`IUM2@n4Tm_Ff$w9-i>$lUJ{w?;r8s"
    "FLw@pk-v7kJ1<`%SefbZIyz?953m1v^6TLNzu^@3%AB{i<>7SiI)nRDa)5xYRQ50@9T24(U?THNbe|EFbXokvh$p"
    "(CS+~WRQ{e?Hx!Llsf4Z*v267We(3+uDHN4JhF5lURu3qk@=@vK|jZh7N+X6&vv5O&48xm{dXC#`LHr+VQQ?CvYs"
    "b?KWVsE|1#FyZXm$wAhYwxn(F|!GNgO%tws}cNK&ij)ER+zGH-G9ATZIsVuD;nV$puDWg!@w=O<NUG<N)e^nO(ba"
    "wYct)MPRinwFZ4J}2(!&1<4t8qY;vX%Az|PEqbA-!xfN%HhSY$1{oHwmuTcEb*|?li=FIhkd)p&RZ9f>#pTq<sI-"
    "t?}Rr9+5k(i?VK=C`DO%~Hu@*5}m<or1e`$HB;iX~;HkZMJ4){N{W{S6GsBn@8Om<s%6Y%rB09wYd6RoH`OD1uJU"
    "8#?uA(N9ICY)R>lfTB6&u~)j%4k$CQ`2|b(FusCR@yj_qXdu>p^Krj}cbTs{@!Nu-ng`)0`(T=&deXsD%s)9jIcA"
    "5-Fsi%NZ|!KsJXXElJdqH~mNhH;v0<;YG}#~b^H215$fFQx#Gwn}j-XRCM#PSd7S^l0?_SW(;L#(}n>VY?4Pb>6c"
    "v5YJFp*AgEx0`!AMz`5&9Zru?yUSOm5;^P^sM(*Gs+-XM6ce8u+8yaMT;0;u;I_bN3lVirJ|wTa0hDDulB;rh(F8"
    "bi!^}!BMoqqg$*3CU@MpAVN<0Dw$r~OFQgKFj1#$Ye2gxLfo=pmtnmGdo&A?sX{`D%D>mx>kLY7{kEr(`qPEmMVg"
    "mzWW(`;5#M{3N3>%eR=}KMEDQki2^m!du1r_m?KL!jYZopYj9}#1VimZpKd7uHkEYLKff{q5o^x0Lxs>ueO=o$lz"
    "D2hC0R|v(5U%7~(aNkJ^bt)}g)*{loZ4^#Iv&OyscW`*pJ%01^tNjxyY<FG9MfrWi6@mjng8ygdK?dEdFf=<b>BZ"
    "a0#AlWo7nD)e^}}1a(vR%$HTrR8)dfCBp?aPTd+k2*ewTQpx5W5=Ft(7#t}%=VPd`Io;mV_)&nhMTv#Ix29dDLRv"
    "4lk(pB%l}J$ZAq*ZqCx<^J>T$==THuX{(`qrKnv_x^x?{`1ZL5pEvbg1q=EnV1<lF(kXMD-E&6tN7p0)c{f(WgsK"
    "3EJc;hDB;4H`?JJ^2}z|1bSsRhMog~=3bPX*vFD9lv!VSYFj!h|ZPbOL-UTdfyY(aDhQhT|s*7Yp9bg-QS7l#<+)"
    "&e%CR{zj_$wHwsyAO)dxvzIvb)fAZwWY8tKzlrycFws7j7THbi-h&u>?4*6JW&VXG2XqujJsBcH6e#uCe-?ALR(t"
    "gc|vQMtX?-NFxrc8HrnWdgXmV(Pg@=M#w&cqR2G{XxcGk8`XCrd~}Ci(CX*;6#r<9fUO<>didI!L$MhfN&B#YO2r"
    "kt11#i%Bq&tq1+jWS0W)ai$9~QhpaXRg{kSw-l0L!j(z1cQ%Zmt5nx8aq?)n(23G}GKk2`v|f{@=K{(#Jh0m$!AG"
    "%802;kOR-I2`^D3*kUc1Q+o&4OSx5-D??}{3CAa8BYHL&KwRufh<rs$Xgl$vSy@@m$*mHqxR#6o3WP45V>0Mo##h"
    "8FHY1Hhk~(=h#VG=(&R}>FHMupG}&n5m>>Jr3K?c_N!HNMqhs}Jj`8YXY<$1MZT0`61dlhp#VY9E*O4xR`>Uxd6X"
    "?LD6lo0askJuu)2C0p<#(vGgr;_1(h>e9+p=cLvMXa-*BPW9!O!mex0AQ0*G-*~oda1-ok<LfaxRFf{v58!d#k(K"
    "zOBPv6lX-fx?DG!=nAFrg*#Qch|+9z=51domR7#)f+g`CqLV@i0XNmMx_P42*ORP2D(0k#8D4MVu42(@4ge_OC^g"
    "r(+#h_u-2Vq(?l(hMlaDFh1|W^6PPvd0)wNMRIs;}h_D;IfhJ$$TjPpxTV)P{HqtbxPip*~MIp&niuH;j8DN;Wb7"
    "B(|m_xbTewFWlH-?)QO(H|G*7jynJzbIz4eV}IzXd3H9e%e6uDt|*Du4{}2lQ}YZJFuSFT)$q-NW+xp5yiF>p}f="
    "6tNrH(`@j53u9Z>tsTeIrowm=T(Ityr(NeWpVt|i)Gbv|fS;5jJXvT`GX(tq`yry=jO?vs35kgQ2T(U+HK6v9}A|"
    "6NC?8|pVtXd6ET<d4*-BZ2y@J{=v;q>%U6tX^YIEb^=?WXm2pTCQMP)K>REwoebs>2t^V$*9j5e}g3dC@Dj<0ZRD"
    "_l^8pwH8M&zN&pVV!W@p1Q%lsDFm&4Rv>iOx4irwe!u*_Uw$&n5KYuvh7QoCUVT&YE$evbC&mXA&Np?P_IBgn6`|"
    "IK54*siciQyXhXlRz=3xIn-|TgNd9(j~=U{h_npjLw^d4mWE)|>SKhHQL_^!tn0<6$vS}Ux_UTA(4URKLF&oBo%&"
    "Ne?gBTej3uj|-pGm8Cbhk}X8VNKgXpbip6ozGP~Q?w*Ir_%6_)U__wqKEpAUaMXIzmm2q>3Oq3{c{)FKUJg&-sDs"
    "*D1&}hu<vU1$=ZAM`sA-_`hB%`aB>_Rt{a@AHMglh#DBG|8YjtZH$mNEe}ilM(f4co|Fvs;jyQF*Y}D1H5t-z4Vs"
    "B{<<NtXwcTJW(3hhfe-lg%*@ry;G{1;QinJp`UTIf-c-=IVJE9{GGTinkmpI=P+DIq8{<E~A&PuHizUp0y}`A|^!"
    "h!l0Cvq#yZPuh<u6Jd^jxxLr<$GFRGL1(R~xUEKci690+%AEZjmxX`4!(GrYkSP>p_iREOij1K#b1LOK%)Q6)3*s"
    "(U>@CB2#vdiMhpd+dbS1O`U&nl7XB52;`@vz*Z~f<l%ugPKj(`1Ov+jrcq_Quj`HaG?s-fxHa7!2L>C>lmZQ8PuP"
    "dB~yMelM_uP1ULonbnP!}wt<00(t-Y<a3C1zHoJCxZbzA0|M{S?l%|vvPvw3_sZ!-}2<)SJ2Savb20wu7PR2S#eb"
    "Fy=FKs%6*T`X3K0G=bXRQReID+ar=7bi0-V@nBjTFY`(rhSxbl3o0I=Zd*RzI&Nq-J9)Fi7{@*nVxNsy0h}mB-v`"
    "X)T-Xr?05r>WL=?lls?Uax`yW3ynovqEylv6d~cy`%NU3MP(M-pF0-H#`ioi<z)5oU*s-)pyZ{~>e5c70#i=H`qO"
    "GZ=C3;o1D#1fgVOXY;|<^06Ya?aIMYqkqC^;XT5t>X0cMZrgKSxD-WGQ8`0)>#xV{ruZ+!ET8<hVV3#@^!A-|egn"
    "?A9E?dYa11KbjhQjw1f_~Wq|DfZB)W4^^!xd^!ik?_D1@0=6?f>4;0<XD0o~~=!`xxSohshWqfN~Q$)ZR_m6!_$!"
    "O7q^=|Ikwba8xgwDZT$dq+oq#a<rN^kP-W{sh%W4^~JKh$^XIas+Fkk^)`vhOkKlnv}Y+B>`%Z9ftrX`7iXWYGkJ"
    "jKFjcnfexuCDP@3zIt6v9@(4mO$*KlF`a}ydQ>w^H$q&h+O+V8}mSNJ!nw3ARM%fkI--qT2>208VqF3F+&CMmzF)"
    "%9FWw+S%4?#xpb(l)AtXnHG4kixpiNSDkS*yzY*U%8D_Fpg#WHrmzGBXDpSlnzv{d}WEqVDy$X)&{J=(}xiepk}|"
    "r;8dm88YJLMyilxXJx3j79UbYh`Ny+@iV(S)|MmW9nRH_uCd8b(gDmsxp(6!!QZ5MA+lN<+hI&P9-@dQg!3C1ydQ"
    "l{K-TdFmo%d<eVe5J)Z}uU<Mn5vn(CWs9qGxqgI~1lXGDZBuBGkO35x=V$dkGOZD5dRvOw3>pp<%^_9c-iL`SL5j"
    "m9+KcU6n!Ewwf}X;gMSe&0w8enx0mB$ILRQ8>?C$_V)c?`WB^+3jaxfB4}lw1RxU7!Ql_heq@s`GQTX_{jVgyINo"
    "U_VHg-y?<nyj{jI`^W`U%QR^z_^_y;qZ>G+-+uyI%|LNE24d`+(+0l^uB^NFihhhj>e$FJ;Eb-t%lWxB#r<mtv=q"
    "jHPt!B?4TVQX-_=>O`AyN|NPz>`~0~FxW&w0zonoA3pI=6}?t-@L1?ME2pkB!R^2MKTUhtg2_po{F3Il__r<q#~@"
    "VflGSN*d00aE-?j#}f4I<ve(-#S*LW76*D755sViEXdU8BcOgTj#@7sB}dLG#V&EB#*=whdN=CvwKp7InTjQItx<"
    "jsrhOd@I|xYjX5cQ|(s4OEK!!;7!CLG4$E;vydu)LzSg_1NfCS!_4GEp3Rv&cfLGQmUL1cye+!s{D@QyRWKv$!JG"
    ">WRZ4sq<!qLR7%&f0@TZ5(UU*PC=Ia9&+{s6#Ib2@xV4e2A85UYe~GqXMqFOpG*wVC$S^{mNnH)V0;;7-WX4F<g!"
    "FqK6J3;6Z%Q#t22Uk;7GQ#Rx81h+O{*&k+nR$S#zg@i=*Gz(4&Wo_Edop;rk-cgL#%jE(@}a#?(pZ!`J&qRaO@<?"
    "o`4rOV-9fVc_A7nA8Lluy>~#i<uAUF{NdnxdDdCOXpun$gbj&?4{=dykl`M))Ql61EZ<!JGL1T}?Z9tbd+Io`ME@"
    "&wts&zn@ZaF8sHB|8X;2(VZ!G8tw96?+^U5-A<E-DOU8hecE52z!yRAC}W+K1g1lTs3r(2<r?@qi6EHPNuOGZFyq"
    "N&MD>oLb0b{Kl;6~$E>ag4!tgdmwl{3#)Mx*HN}j`r&T<BBW*B!1GDM<ANj2<yc(_54&U(X~k<3fj6z~Y~1V(S*)"
    "6X~!Ep;Ga;dq#WtN?$G6aM-Bix+!Gdk2)N)qY5>oc0q~)wZF&*M#E6nm#W#6y_JPM>%}(anqN~R+E=|ODWaXqokA"
    "N{0$iS{qKzYds<FSS`Piw)dFSF>>T7sghR)fc0CYQioV3k+Eh%}+T<i2H0a46prPa*ILxIc0fFUCk^10KXa5r{G<"
    "<b;jYJ<<**C|}>vIr7eB($if)(49Y&3$DbWbb@7Ksb4&0P>rYr;KnhJsB@&>qvJX$Kb(Gi}pdCt<a?QlGEM=%$aD"
    "=wbiM_VsehvYB|W@R~>=&~Igj|Jjz0|AgGeVr&p|9TB5qs#KN4+vimGu}!*f!&_&p7r~atMj1Hpl?<}sEeW=LiZW"
    "Y{nM8s%#wg+uy^i2^WZ%l@%O-h`mOPXSG2aR>CGI%dY*Ff-iV7$MJN0vW>NeC8YToMYad!31l4siA0U-XzU$)b$K"
    "7zXRbTYrALZ6wV<T+E9)3A?eH=b@J_2g47ChxL#E<B$m^Tio6_y$&|M~N0o)bk&Y(_{<(*xHmo+E1Ti`Fj42D%m&"
    "vJ4>t~^ftQpWB^<$FO03?F?9H!sGflRA&S!COp%djyizt(eyl(&QJZ^-2?U9C8G~Eu{^y&+lRZUIuq`LO4~}{kir"
    "AK#n$^Fx*;a5SxR?W2rs}150~*EdL3gu!waZXF*)%fiQ(ql`ixpHnklO$cDHdZx=&j^pQzRdWM?;F-bqI2|;%<v$"
    "4pPk);J|QB?7m3us|C6yP}sbj>(t?>I)AAj2^<24y~8^zdf&~C!B(3zx$1U)`mp^qoR%Ev7j;-}ezW`QJBGvm1L%"
    "aNO4V8_WKEfOE}?G9z5g=<ko~|RQ(n81*y`|3>N`Ot2DCB7OGCh6>8l=Y*xn&sTbX6cy)dNM^;(f7@#-8-?fS$Pu"
    "Me+Aw}!n|un)iu-C!!F<%Wr=(kR|azc(B<LM2Njn92xmN?hb^{I?}Dx`yzcmSMRoD{(4zahG1(E>*4j=G*G1d@b9"
    "G;nT%D)TWj%<2PgUkG?0GeE0R-yzub9Z03rbrdToJw@yJ`f^Ln~sSQrtHwj=ZzBvD6ox<DWuaij<72K;CBwqH2n>"
    "kX+3#rWsk$jMK@+4e$+=^5Y<M9{wSF}uZO@M`Qc-?s4C>(oD4?!7dK^SfanFn8*H@UQccYCw#KqszCoSRa_(YFmA"
    "&TXo3d$qXTO56cb;MeG#kua8JjuvAMCCz$lwDIQo&&YPIVQ>E=v4P<!H|AOS!4!c-F@XZe5SsrYA7$iLNaY)+Xn+"
    "7@%P&$Ol+l8Dw4ZHxWK+I%JK1uoCJz?lo-LW|0hPPuq>H%*8lPNEvAh#PrdQkj9o2Z#+fG6V&q%-w9X!3oP>Seqh"
    "2beoor}{rU0|RZiALPVu730@`cc@UASG|ZcKaLp!7V_sm@yPtqCj-mqMQuzx6D*AM59(>9d*F`U}5EJE<7PMtZ1T"
    "KTX~dy$YojvjXeK532E$0NX8&7w364tBN9f_N?xmlQ=^o)h=aHVpyM~k&nf91&e;ZMT4kUaT#PUVs})iR50BD^ik"
    "&CCQBWkoLJg@YAignMP+@QST4vS5B2$CK&|Q;Ovdi5j&K`h?6WOuIoD<%a;K@kNuIRU2-dD-}WH^~j{gJ|vJs(ft"
    "Fv@-y>kKXJdf6CM9U1-x%l0%%idjeDWrG-v-|<DEvF+%TB(&KN`4taJ(L_=zGqJ!Lme>ufJ7W72%6}>~+ks0UcQZ"
    ">uVZyS|^9x{SLEI(K@f@C+iJZ5j;`+(#3OAaRs0nu(%$bWX!e-5elk?PW-M+JDxnvZpo=UJ*a>Ta6%Zs9S!S&6tn"
    "lP;}st;N3!XMbM7!^XSgNfbKWlmMAiqe#1FLOb0H$}|TWnAPzEf;YBTkE*U^TiB_nvC+%WOlWbhrn!Sd{=N)5+*9"
    "GAmS)Ub#`&eFJmP?<Hk-Z@U1K-+dIP<eJeT6hj=Ea3>}rOlhS>>G(D=Gj5Y5{uD%X?-~;J#8wH42<FcRzm$+WI2Z"
    "z}-<r=aHtuO4>aehhZzh={7$5Uk<BpHse2-y-Aa3o;OsgjC!zSLsKv38;qwttpzsHIYi3!ROzh|k>BH_NLM^sqz#"
    "wmA4yjyq9%=_!A`nA54^1-f+Ldl_RS=}+=f>YI*WdNi0>hIQ4jVg_i?$@u~}V`b9*q0g`+An+yFjm1A;Jz?9RlLv"
    "u-2)m?|JtKv#VWpwNltQLvqhgFlzn3_tOxQ7&gk><{WygD$37yO@3+$9(p{dd)upy!9obDi81@e%Zox^Iba#e>q="
    "z_(I18FjzB<wtf(M!ggRD_#Rg`QHEu=cFKpfS-(3>K*Dm_?TgbwD8e7K9&UlF4KsroIy231ZBgc3;t_+M{$R*X0Z"
    "kYdJ&glsa7DcMd>7jv1B!5Bb6`vPHD^V-M&u$4}GjtQe9>Z5^S)90ZWsMrRmkN6df^c0Mf53*=Hf8j=uzOBWubyq"
    "q#-0UM?!l1eK51h@un>{hZjhL!9w=R!*z+_Zh%Hdd;3&byjCvwmL>lL{EX=gpEVVGG9?eq;F*i$23i56|}puDm&$"
    "EY2_dyKv|AKHZLE!xxl9v~RIH`~z!mVp&cNtzm)8Qh${kAQYy8mwnuRqwGpM!vde!n>%OL`psfz!(kn7z&sbjnL#"
    "jkX1c}xK<XLV+Sb4<o+X?lP+3yFC(Me<IzHpn{)DPA^2H#9cCr8eI6gdZ7k4=m5z!47s!u5Dsf>Js#DfhPsN`}$V"
    "@%$F7fz9dA-VvK6zAlA$Gf$a>>zoeAHFsz6drdl3pWTdVdOaq)5nO{T5hsOM}d}>-^m6P-CD@kpr_sk&;%#MU1%p"
    "Kh*K{YG|I@lG1g%rk7`*+7h&qUm<`;oV<WE_c~b5#QmmKA7lUjB^U7Ev0%Dl!iA4R3i_<0+&9auO?Bj_iIg)Co;|"
    "K{;FLCtSZFA2s8<0)L2z|hSG1Cm`JIpDfo3|QmGP6d=QWm3ZtV7aknhQSL{mRq%5n&n~@dDmvv?R_j6?r%7(+#Po"
    "u7pc~3)J^TRD%-+1X;px-iXl}IPs7tt}90`U=c+7W^Q8k(b;7FOl1|?oN6Z)!_P3oeU~i8qzs^-kJDVrWp;5tA|X"
    "V0%XNW?lBHQ$m2zNySX)@BD%W)#o7s1yCR!|I*c5=tL43T<jyw-CRQ@UJ&5as_P@*X^be{=##Z;PH<ijZnb|e(y<"
    "yi6?FN*UE6dMKkkQWMnxV)GQ^B8dg*26NiV9lnAj4IoZXv_eg1aiuXuaIe&kI&~9$X!_L*0m5WgGb-+DH89T4TXX"
    "Dd{0weejT%sXm8nZ%u3)$<^{=7CjzWXsqRSH9`m0uiY;hcO|(A7n!M(5Ew3R=y&5KS%ouyixy!49%FSNFG*GYt?Q"
    "a3%ZEpgSUD?Z5D=V~X1<Y?&!$-&ihN*rNq5zt$xFYcwk1eq3VRjBbv$+mI=MZI1S&K3tHk*qS(#M-{hE@b+3I?!_"
    "<iauH+t9frO%(2%>68k|Gh|@7f=B3tSj{fb*m9m>tg*5PS1aND!UIh9pTodm_~f|aNq%HgNpChOQ5u<YYqG+X%Y_"
    "h{8lE;dl@s1=G<;z<CH4*a$jDtnWr@Jt$wXem9CpR7f+8g7{P;MXOG6>!YN0nzdMxIkDnX)`k{w2-#GMWor8i8~+"
    "F6Zow#Kq^|AvxCGP0HB2|E)9Gky-?sO<PaA;Q@Y5i=({D@j2SUd$xM*KW`{;1ZImj0zcYc;4Qmd7v~+CgOyrixOh"
    "5A|E<u{{)q6a|L61Bk1Hg-ovxScuaEG1Q{RNb97B81BRz{34CV*wBO!`L>6cr4)COw1Bi2`jtT71OSutwu<97W@d"
    "$IP#XZ!c;r4Qr-+(oa$OMOqa9&jSNv-ChFGa<TfWvrM$wTCD2exh_b0^;pTE!fZTC5G|K0~zt-Js8`^#Lf6&xj*{"
    "xDN_VPQo<*#xe;h_-qZ$MtGGxgN@Bv4&3PIqed-uD1xfkp85vkTqeAXVZ3JF9t#yrKjZJj?LYFkg>g>sFvU)nfKH"
    "&)GPjgYgj9Ih+H54HCUB?A-Q{{GfFf+tTP}H!VDE_@WT|2jC7{bsQ2Q9cvY}jup&M7mr-WM@9YXUu=JFd_F>yCps"
    "25i9h^C}_vLue2+;N>eBb{_HXPuI5Bjov?75K`zX+k;)j)0kt85n&s&#Gw{H#TZ!yp&6AqA0P@Hr=2DFPQ~wmjPO"
    "A_z-HTt?<omPcfy#%LM(<<43x}t>l0-9Rf4Rc;BeevzF_iMyfjm_>bO-hQjKxFxFGJ`to8rUz5MIH|rS;Iib1+oF"
    "&d@{$TYNFI*}7Rj<#Ki`mEGBklvzuHjll-TDHz^AK656LeJ1XVA#(I$lU`79~8>n4E3ABZ|S5xYi`%g0AIHFmt?7"
    ">>g!+o7C(uPr@e$KLbORDXTD!x-N{L#cT@}PBIQN8z<_!52uNwM`CRmvAQ1av7tCRmiSVLN1q8_aI7P=i5QB3<E7"
    "}97SJgc-Ert>lOLi9FrTW;hAwAss<J4{WfQB#3C$@z!zhLh!j+mt;FR_#LX8Zl8XZN$T52g_uNr$vXCl|>Qi)qF8"
    "<P}7LrU4s>O13j^~}PEp$M2IhZ7iWmZ(O|iI_?@>s@T<3ej!@-aTLHR$<-;d@C<6__Z0{WUw-%qB8x7kCO(>={HC"
    "Nx&G`}LOdqigu-qRR0-W-$g3^N5qp_f{$t57n`5xje7PvY2Dd@(m@45E6K@*ZV<Of(a~UXlq$-uN)kb_Rti^KLwJ"
    "e8y0JZ*IG`+E}lq=lVahfB?7p6AlsY#t$t=kx69f_r)-caJ4d;p<NkDoDnDEqfC6{#Fa!ocusc4UR)<ORI^(KDu$"
    "q{)-h4>zc=C-ff(d<OM{Cpej9m#&YN)hv{RP~sx^iDh!jK1)9AGoh*~Dz6hWah$36LS;HS2ppxTwREeK)Pn^68_F"
    "h}|At1_iUXj+NIrnFHdgEGSlp^-DBEQpvtmfchOTm0K~mgNahVC*snu`j471m%yeOu|SY7pPr;b&Z7mCvHT{IeXu"
    "LGY?P$lKQ$jsraiL!b)NfTUSSO{2<q=dy=rSZ^GlM{>R!0Dpm@ll8pT$X-HPU11eTGD<bQ<MJU4_eMJJN8Q2LOi5"
    "ee&DWoUyg|$oWo<3`^Nd4q;h1)zzdO-&-4QsZ_yczPtEcXYRo8+7_CeE@Q4vGD{jImmV|>y(tfS_V=^0;@QD*NhB"
    "7<>N!BX-vtv$VOD&+iW*mqc`-;2~)~vjsou@-qpFhGIY?Fm;dT~`2$c#tD*cEH()d=#~8!q~)*sve8pAXR8Q>Ko8"
    "#*Hfx$@}93_mMiHE4~SjFT6ml&qxM1I>YKTbD1yD5b}VpC=s5RZ{>Z92qEzSg!nLF<;#$Q<zzW%!fRq73<2}lM?D"
    "2urK?PlRh&^JP#6Z)tPk`e$ccPrU&&y*d>@lz`CQ~M%YkNCNVbl{ynxMtj!p@kK*_|+-S92`P5h}S5`gIQ%mlUM6"
    "p4cdFfu|Y$t|ItsjmVLc;aDwAPuL+e=FhDYp|Ihs)KcMGdA2t$b9-X%?g(Wjk$rsx|5(k5$3o-z$J1g(q^N)M)os"
    "g!VB;=Aid9<0v)yi(5hbRAv+n_X|S3YTIOJUpbo;);zzyIXA`tB41m3#6>|*9PKF>UEzlYa{m(BzN*}XGyB5E>U#"
    "|>#nf`TLXP3oQv?>58&=4>RRi{uVn&+i~le)-CX6A$9d?DhChS98+S{#QLQbe40Fpv?439<KW+uVAx-V+H0p&0*E"
    "fm=)_b%Iaxb*bB2!Z8XCkZ{JTBB)I&$89m6jF7o8?_v)IGs<~RB9UM_Ea6Oh%6>3`0T>+n6G*~xOdu&)*9|U>buD"
    "X@1G$#rZqgns41?!YcBW@?Se8pNx>vPB;wJqZrSmgZe9k~>C4I!DSG|pP${tLgPr@mL+nug+yE-D0D9y*`)~U=#o"
    "I<o1r{S5mf+mqlDB>DqwA=DBo07ulc&%5(mZ|z8`-wtkHSUBwOOr8yYE<`^iD6*v$m;Bw1Bl>kb0?G$C&WS%oZ5-"
    "*EaEz~EJiOXT{S1cg<mbo=QHdb_7ff%F}0k*5uT&H3MGXhM_QfFB#I`-$P^9{T8rt_N2_sKcnz=lSu_f3U|7Ou_J"
    "-(=&_w7l-Sn4}gfq8SGL|4T2|cuQ`_lOAB_@|kC2C31YeC<^AtxBgO!xI-dI?f@>ieBx!w=a)WR0JUwKBFFgzdU?"
    "y;3;RMD%vKrj{x{6lLZ_l<_1;{&0gwg{)$*MS}ntSUj6<D04|&2Wn&Nu{^w`9OMPuqBGDsIZ`LVb)C_$O0sZ>*Ai"
    "E2rNKnhb$gMEE6ky?;rMzWEvXl!{Z`DTPOLBOb~svg1*hox3rAID35Z>Qumz9lC0m=D2H(I2qUvz%U^Jgjwog*Rn"
    "ZdxvJ=g^(@m^kBp_3ksp>~L{QZTN6<g<w*^p;EH47<*}snnM%oTZfAg$_)kl9x_|_`0XOKJrXcYHQB<p(X(+?!lZ"
    "y-=*dcHnEYI#a>rqtSJ{GwcV|!)2O|Uqt6_r4zH3q#h`I;o-w)71~SHf4xh&SubgFMF_DSw3v@5g>CrGqDEg?fqb"
    "y2?RPEjrV6;Hf*mQ9=1a*p!Z(zR_Eo6Gd;SyC7XEBBiv4l1Jj5jyPvZRlYPtZD_nFcJ*kZBEfF4-1cV=QcvQD%(M"
    "JFoYR^#LCw;mGA;crwR5jPSv=`;it08BedM%0po!YsPj&3g<zKm6;?uS166QS5WffKn$XsS77e^ITp*s){8Nl$m="
    "-EYgsowr{ucHC>4@2AVInWA@iAu00{)XsvVlw>KSnw@u~Cnv8!fcO>8R8Gso#AvT|(HKIb`N#aOz>?Btx(W%SDEl"
    "BR*)N;wl`>*o*v6wb+=OuQd>fJ!$Kkc#>cDl$1o=?zhFlyj$|$xz~~KP-!VC(rRLKbuU*fo!a=u2;v|E4Xl^UdVN"
    "2thp+|tjm?^gV`#%pf&7i$9T$?syT3|%5p(c1K*J-B441~Y0TZ|b6nrfV#cRwZN#9^-Ap>O?(}WfAOky+eFRdsLw"
    "vTJLYAtzWl?H$sz&Qrck}$}nZ8f+%0`^!j5j`6G)u=#jWIvCgW&k(o*B50dvlpFW|xDJ#7n50kmKkV#D0uJSu@~9"
    "95BVM3^nkIkRxMug%>i!FhLh&uMx48XI_*TX+mZkNy1xg(tR<R^~?g3v4`DdxXh)QiggCVOM1v%#=Wbha*YJB;@Y"
    "|%Z{jtSw?<L)#Qo->pIGipv8T!9C4sTL0XA6J=Rvz62DA;-lY~|TmFsjXShG12ccp*X7-39o8*6CBq2@@iuGiT*x"
    "Wt($TVF`vK;!X{O;q;@?jbec_q!O3QgXD4YiX-xOD~C|;2}hFGc1x?U0nB&noP4rznEin_5$%;f!88`8WhCMs0`6"
    ";0>=|Cd$I>rbtL@f^xgP+t)#>*B_(zP<borZ7`*`&)tDibtI^FRz_XKqb$2*HE&^iE!X)z}7-5dacjl{h3TWadOK"
    "dASUYv=`6t}lk4>5ZIFOm|L=WOx``a5y2wIhDb%j^tgo)Xnbb%$FsI+^dK%*qB&T7oBVcm_*>m|nNbX%yYA0scg9"
    "9$V}j#DxrjHbPLC7#af*VtVCZGkls~&a&xpI0niq7f1sb5L}7fE+U7Nli|m_(QL6d6$oo*-{BXv;J;n$wE^6yf&E"
    "Bhf<4GVE5Ilr#jWTLvol%wcXtSq$@WO;yeB)yza9G^SJWx>7RzZ35Kgd5o3BcE{_n=L{>d>teF6_R>`N7fME0OaJ"
    "el=Dvz<-%VX7Pkw*u!Wh|31!uQ<ODM62`MLCjFV%5E2pq1|o+g*OmoCYZ4&WA!QwEPz7*%}sm1rCW+%IB2PRrlSp"
    "l-;r4GBgP3Kjuv}I;9odTOly!a8Pm&17L@2-eH{wmR0ZD0Q^BwOZwQ4J4;o6F<-B#74L>yS57-z8ih;v2MTnX~Jx"
    "dg8DY^^zO9OjJsgD=30MGM5ljuz907WmrV9iY5x`NPYycoiOYBJMo2oR?o1&FZ#GYv<Up_`Pz9#~Ff+rdD>uZJA)"
    "X-5!H57z-->tU<W*!7Vv&&bX$Xjian3Q_g&|J~z;y~(i45!<#o8Xj@AJZiT<E&$;Ve`=sFI>!RsPR$NG9@xVpebc"
    ");t-no*af6<FOK-$K$CG3uX(!t}2I#8G-<~!rgVtcZj-VLXLm|J(ncxHN9tKz~Dz9Mo1h*lteUp5fm~uwnwa}42Z"
    "8TS}CopY_6SK$MWE7xlZd_EBkG3vO!0uz^tSt};35Avi-}D9_K=k3x<E~m~ll~R&zo0<eES$0P0PLLVd8j<^KftH"
    "t-#U?<<{<p7O*9jF2&(QdBNJ>$#GuZQ2{8fk8KUt{t|Ou@CBad@dq;3C&H?ag>~C>~=<{~*mmG7FnkZZu^V7%0-x"
    "s+zJx*=tS5BH%4)g|+y3{}<P#1<v_m%Y6tT1vMkBh@y)6hL`Ym?VMlNg@WMa>xG5}HA9B!l+|I@xLh7f$fX8#ra4"
    "e+N!S6HS9dP#cMi#G|`NRUMBwQG_<`G8Ge!Jb+phTowX`cIPzpzNV($1%i`iCd2!SA6$21(OiGF`GI6^BEdraCpO"
    "{U-Xy(X#_?Ss!_xic%@((q2bwM3UtzaXG=X+NT|GQF*xNnXd+x)s(F;MiJ<GlKIdq~QflgHnZE6KVUxVI}ns|ba`"
    "?!ADwecXQ-f&e9)A8c#R*#URSZ?cyhV_F49q(x8;P}Pf5h1<nSR=42?&!+wqoHKR@QP@x56%jI>7nBO8{Vp~caD$"
    "Y3da!XTb`zDY}7*!e8U*tuq%^DOXh!xeF9;@+gkleZy^l&bBOLABE`7BImReg7_GEZ>7T&`v3UqL=<!Yt#R~8SE1"
    "mkB!;HZYa>WBH24lKeb2N@lj$N8n_r5=^Jm#YA{Jwv@|MSbeF76CGi%#Qf`zP;i_)pW_^A1>$E+&dovw8PJe#J6g"
    "n(*b>*>d>4x1mwrayE2xJGw(0)yx@7{Ge4OAnm9HY^-5-SB)eTv^M*#Y2=xT))RkH>D=VQ7m|9_<KYITZf?GZS4n"
    "!oTf-gRWT|)6U~Bey@LY8Q+RfYQn@?BGXASvL7>|u{L%>i37S(Vm4bKOzWfwXw+$<eymC<W!HU|*zww9<yR1=pc9"
    "iu_0hDR)2V!!&acd@zU8MmGrt)fhflu4<L2Ipw&nG<4JN+hNlDdnwI98PqZEj0s?)u)G1O>9VOWoJEG-D^kzZ_+A"
    "KbliL;O)#(6{P>E)OJ2_=pRN$S%eEow2shdpUl~(Zh{pdjT>DaXX_rE4o)-u*^8(9Br7^7j<6jS7R}D|^!et;++j"
    "N3K|F{%lZGx?W&l{`I>!bbMy<@uaeAMvmWb5IkVm<EudboS|atER7x0Cyun=uSXc;NBFYwp!V;6cA^S1CU%;GNsF"
    "R4s&x!aoSp+%?AF&{(3P$Ki=<*LdX=-)tDN>0ae3v>cs;mA4En8^DieSx4)JlNLq6?yB_L7rf>d+qXDx)c3$lwy^"
    "_v2dz<KRE)cvx7}%Ddd(;EX>-%-{W*H)ZQtR`^aTn=g?^v8dCU2{vx$Bl>{Yv^>#8W{U2^+0y1}t^Y*e4`-J4<37"
    "Zz>AuuWVp7%A2g;Psj1jEqPd2F0@t`2lz*@+{;i&izYp(y1;RUa@(<q081H^bT_co;nOie1Tr2-U4GE&&w7NR;x&"
    "APn9AtzvWlTNyS&CZ5@b6sbAy3iqh`eHm~t2-RhWF{2=gKGMIa!2i&@xM0_O?smITQ-xp}6>`h=X1SxYn;j{Ht-+"
    "F4x<|;iXUW0K>J(6&Z1EqrPfq#|A+s@5b&?mToiTk&X^jV>|cXyfg{bDdcQ?Ch|@}tDDFS8sRo7AyOUpZq~vOs6p"
    "tX;%=_oye2<~ks=w)%zF%Byz}G)(UC0N+Ly@YLTXHOP==J^z=vCIksq*$W?jAL~vCjp{Ek6BR!>8;Y|3%(o^bXPa"
    ")Gw}$h{c91-dZF7^oeGB&uDD(JVsZi-AS8RitO=YbG3e?f%NDi&oI;x8ygvINQ2x4ts71`c($p<~y!f8ftq3n@ZD"
    "~B|uvGZN@83SQfnnw&RrD!<{3tgFZsLovbst5j$aT|^GKdc+=Y!}OxZGmtH{L+Nc_akSgRVg&>^v1BeX?y?<Gczx"
    "B@@n}k0)Is~Oxor2s_;an=83xZI1_bP7{AoQGi1!)o(VdVhMVzA{mU?QS)rYy=ejb*mcQcFPwcS2=6$|J7q542*A"
    "fCqkwj;62T1gP-ew#B*xC61HaDJjH%@=}cMF(nk2#|Cy@lTO2s<K#$#UAR^{Gk1*F94pI;f(3K+(%MM2<t^!Umo8"
    "qwf7D4=RQw-SVNF+xU#Xw3reM7&~DsR}$Cpsq1FN;bglc<q^N)PpdU2lU-J_*NM{XDwb$*m9)2>B!BKyCW+s*yPF"
    "T5bRRx`w2q~g!#C%QPD(*r1V1Jr2BBVN=uMwoqNC3wwirPNmGM@mQ03QU9mA$N;VtEErY>e`R!QVGyC_C-BRWbAO"
    "?PUizKNVFi}S7vOT^Flj&b@%y`1v5s4AwnWIP}?`BAuqHdBGn9Ydu`hSn>rFJg}UccH7Ubn))a_0l4edKA%lfHVx"
    "R4Gl!*`8YYVRqnEODXn$p5i7=CA!N%>rR2Pea6i`ASJxN=+uKa6VOMRdD`*-W+;;Wat_+oE9GGnwtWy?8<e!EiO3"
    "+wyT03rKR_Z}GWOtm6J2cg*A09cBbYQJN$xrd)8kx>I6qPPuGTkA1HatqkI?>8+Gzt8I{<yAexQ69sX@X2!{!}e0"
    "4XbfNt74Q-7IXP@cuapZZ+ql8u9W7ZDvtwz-9VgkN9DP(xd5N9m<ybR!#>SDQ*GQ_uI|(Vo?itP<3Rh4YvA8P3$N"
    "A0Dapy#!i^@bqvqOiuGU$jjALifyK)U>e3|-Cuaw_FF<(bHzo~+51b!tI$)*)jv67C|2^I9Op`@>^sDDjmoq{|ld"
    "qqoZuBENlukyWn)LmsU*3sP8(%z~2RoeS14c=RD2b;hP^Q!1t>#KNirH-1qO6NM-oYCcYnby$dXdRcn=Bui3`leI"
    "QkYn|hhNZ7jP@JOSMyc@B3HwZQrO)C1O??jczp~F^MB$|II8<8_Y`LG|-59T{t}0)vZ2f`DMee6}V^x_^5I6n3Wf"
    "&U#J_rsarJ5Ot1c!RpKht0bgMxvgn8eHZX%wKq)wd|=Y>FbD#;Z7#TWKSs_n*Li**0dYIjo6l+T0KQfEjV1cESyv"
    "ztzd4NvqYuGOX&7W5f`c^at2mYE9pC8N0x)MieNiGYldQ0u~uGF|K03r$k0){r>#<x*8<J!>tte)9S(?C{YV8BKx"
    ")~L`Ljp;>;%zf|QV=pVqZn!%kOcuQS#;qmkjv9ra_|6{>x0sCgZE$#wOsfhc@N&tqbE?M^Ef4bzXe6<0p!*!@EzD"
    "LV~gGAjBVsk6M%#?`}_bV3$xM&9{+&82qne+B@$Q>ptyQ5|M`a9xMcZD2RayF0(;!)fvo1R0Y`=-<V}K+9J0g62a"
    "su_J6Hu7}<M@lffMbBS5(_$k?BmE5(faSIKtnj-+QEqvm4{+ylBoKI@JdF~tFBw_l%Xp~_(DPuWWGfC;+OhNBEm}"
    "hxLIX%6}2&OJ5P)_X%4nZe;S`C2X!MMqabXkNWCmK>NgF<g2x>NP~s!1;M*A%M(EL+jnOV*JkF3tIuH9V$F9i$8="
    "I|V~IU5ih?MDtVW8$X#NGLL)0zgW(qKeQid%|)0+AHE(8CmH_mXw%`ipH!Wdr|xfcA3u7sgr~N<n_Ca`ohYtFTRr"
    "G*K9%=lV%-QuBN`ryYz~9A(_)-|zX27WbFH6K6#E<#sHe|xDmb3rAO?pucuTxA^0TF2>{pLiu?8L);{8{smDY~Zr"
    "9~PoOOE=&_^N^Yo(&vL&38h|0l#3o$)AD9#C7>&VG2jBV}|up?`PSNjiENiE@qBJk*HOa41^=Wle`6+CiYLhpwZo"
    "67y_=-R{)o~VGvR1MX}8n5~{Xg^5=C%H^%70^US9c3rpImKhSj!{bVvdBIfFpU|p21qmY1<oG<k1+NNtH&Mu;?qV"
    "B9$POnk8<Y%?=ps0!!%Nov0Q>Q3KYQ{#63f@BEnIM2^E|NK#z?w|PMK2X}cf1OxonbaQ>u1~Qz|>tU8?mE*z&bLg"
    "RDsaJo9qOpB^{2IELEJ-4iAT-#JOADsJ`oI!GZlmM)Lvb27gfLy9HI)-ZV9D$7CF*@G;BFa5I+|4PMz)7PNzMZ^X"
    "D{H$?D2>P$3sN0>STOl5qj8J-yl1B<yc`?Jp7-95gXYnP`{V=k1*y}NUKa`?J?wD+HH_KrE++UrT_{Zq%R!ixS*_"
    "FwIFU+%x!Kk;2M>>a_nvu5A5)MZk2O*wMxTbF+F#A(yB{|Y_)`*Qg(cMlIv_Wt)tWTdQeqMXw~{Je&A?%xag%E+C"
    "OY{+6ZgP?2eHpWv!A|C#>cMus{)RJ#@v^f+}Uip*1ZM@68)>Ljr^y={W-plUp;c<*)QcqV#(OEVO{~>o<|4@mxr4"
    "e+b4x6U*G^%6unTOpj&4|h)8z}P2oQ>@r!)-Qn_eUC|v%y>Sj#=NJb=C9Ku$ukNO#H!Oyx7@)`3+C3Uenmv-~HkJ"
    "jDK$8wyrkCZw+NujAQ@c_nnvf&%1AqcYfLPw>|guL+lOCfcvBtiURIwvh)}+%4*tW(RbVua0lRL5rlHA*=q~z(N8"
    "NTakTe(ZwDA@cX#LI%kF+<d7Mk>2mAV;EI*l4IeMH!9KMXPSsXKGVNuU6>(FD-;xb^ouxfN^R^>!XwD?#eC(&WAu"
    "U^00qYEXKj#yJ8XSVx=N&LzY*UfaW_v-b@U*TSQ{qnCBR@3xDAFGR8<&n#7#2em<YoD_loHZ-;)v!Wi19NUq@%Tq"
    "PvemV|ff>u{+c=^n#woK`yX#rL99`YH-g#zK=kIEBl^>lL-c)$}ETOGgl@jW&hy^c++JPR+YV-|$3u^!>&aA;rTz"
    "S#lP~3-=scj69+%akO{_vtTD!07Macr{P^zFgbat!->e=cYqQO(G)DwD5U%)?TfEdO+oEfDPu^GV2JqS?``Nnp`3"
    "gz%x)H|ist$p+}GptS}1V-m|?b*YW5Fus|{f=Gs)jgPfERLqLLLnYqSF*X`kXb^&*29B~vF@tJs*RDU6^4m_u%?}"
    "7?^I)CXxXCr~#TA1e#z2gV;V?@c5hNsq;$)X+`D}KTJfN?h32f8Wqs>jWOQIdF1^dlK!gKsr_5}ZWa`M_ezwFaE9"
    "Or_qatJS``ry2|pP71)=xHO+X!PSSV%cg?43a*9_J6<3$M=zNf`~}^afL;QZp~?&Qt6<h8n=A$jd+H-eLCLTec{7"
    "2ibovLi7ydO9INnl3CX&3F`rMn&XeLw^XC#9Mr8!k><W|gVkw<OA>+JZdR5v8aVStj303t_PlnWj30QSI&+=?!!("
    "=M&02+&2$>AVN?Sb&Rd_>?$lncI{Y*zD3^9=4f<eB+kK(J?c9LEz6Y2LfqV%%TYbjQ-S5sR_LrP}`SM>+<G0Jq(4"
    "Ke+$k$B%6)jrpT&HbU`<u@5wPb)2hN*30VJk!LPI_5lGInawWW?;9t^!<9`rXa~^<85!q#iQ=Ujy_V@1O`6HkVnY"
    "kc?pvFiG2yFv<FVNfIfyAlqG3^$K(&wg5MkE5^iuO~!paCPvx`a5!?Vk<Ssl{_A=%Jxl-BQjO)b5w{y4&j=^9Okq"
    "@1AYAm2t){%husA)U6E4Lu(>(%K0Tjt{-a1Br1=nx@5Db4X)zGHqB?>+;b+KdZzxeI~Eqly4{36MIcaiQKcMzj6g"
    "L-xjxI;tr}A`Nao>e5T7;nYx9&?F27&$CV~;Pn)aO&U6*5p7|ctzx!M3O+)eia1<L{mt!`w^`s+fh$BVDf!_IB30"
    "fGr_LjZdr_00>Y3G0)y;YC(=}K9}IbzX%94Gf_j14v8o^0%kLso>=OL>bZD3v8Qic4*Klp$z~%QqT5O**YU9%y@F"
    "k0us?9KtYXa{*P4P-K-tPQfpWrDaQMHXC&+hMZ_yYuPc@oXVXTkaXSS$ie(dFnE{n!e&(Sae@hSg6s*b+FI4hCbq"
    "ORapP`nu<bsaqfgan+@1M+R-A#H7&pY#-6-*>8>gm{xn*K%70dOCVJIqb(@9G!eVGZTu19iPKSd9oZz-|$pS5I^k"
    "*T5<m9;pZh%N^AqXR$jSIb}NyDa3}w`zY7ND?+dY*)`+F<v<N8XAJ`uo2s#Ile(OCp{!{!_aAS8qm`hSHQ)`<uZF"
    "*9qPos&^L^nHW3dlP~L*>IhvxwLwajs$pZ$UB(68=G^isJvMo`7Z(Uu_`O=H#biTI%yr<1&CKris)?v{+9V0*^rg"
    "lC^lXjbP)+sXBW#)~F%KZphKa8|Kjm8~PL5}iAF;Z+$&OL%M&L^WG1|bTP9bplZNKP$K`;(F(^kW;pFt|uKqe^h8"
    "9}4O%ER3wMkX@w)%0ZW}4Pg0b!l0!=Ij32X52%1^-w8BgQ%Wld1B`$W1g<aD7Z6PcQ{T23tilx6V>H#$uRvu`Ub%"
    "80RTCJ~3kaN8`r|WoPPoB{)02$}2EQ(ni6WRNoax;dR*_y}1Da|=m@cs1t@ply!S<;x5QQb-T6~4Lq!%P}CTCaJA"
    "JrQ`)L1IJWO0h<;k%_7H)D3&QzCIxI5>V!0gRJDT8+^n*~eNr5`BeIW~p(zsZ?KbV~`YGOjsI~l{IjzxW&s^@5dP"
    "yDaV@u=zX4zi+?Z@>yK)w@M3IVXT1-|a2XiAwQgU8ULNo9SPcSbUWBnCcqZ+f4><@dup;jkTbu0%38i-?>{m>a*M"
    "h78J@*mbl^||!2{h|P^p<}gf>?Kd&B)!TNyDPs^ApeIb4_!ufT)d+MDwU=%T?NSI>e~E^kwY>0+X$yCm@@y=-xFC"
    "p{q;UkMm2oW<cqj_qyZBWz7R5rI=@q;Rl?7ALtU`ZUhJ$(H!|8(BBD5p@{fOG|Gyon%%6t*c)2|h_&pEr1TX+Efc"
    "VN%GlE-%mg`_l$#!F@V%I&utQ`inSz?r<J?uLm5zbQPzicspsfV4mG!Ga1f%!IZ(cR{B@&|a9<i*j147zHYEyn(N"
    "oQYcw&>4@O%L};J|A95a18Q2nnx=+#uD-zA}L{1&unZY!$3>)l9|?f41PYRqKUBf?-{)xxI1!{iNlQO#b;Qyp6k4"
    "EH3Wr(Mvg79O13s=F;6x&lJ|(X-PIZadHFseM&?DU4vX;z?3AnAQt?kh+~?pPY%!vO0)(L?2!sBOM~yBs%mo;65!"
    "jZy?mAmZ374Tdi{NZGwk0_23^2_9Wlc<RUI_(5;anoW#ddV8owowfH*vfFg>kR>Y<}fr>XuzyAdZksHhv-$i0wEW"
    "pgU!Zc&j_N`(tD?liAg4+DFC#<ey;4ZSrWxa)I}ilNl96la+8?H~MGWhHKLJ9c!|NKzEdrP?{3Ub|-r~PQ>>PNX("
    ";To@e-7K>1F43v=}?8|geS8UG}3^v_xjdcWt@g`X_sU`q`DjnFi^e{j5abdnq%CFo|}+1*R_4^9q^bb_Nc0E)@)J"
    "1^ht9Vd;yq{&~J73-;@?NI8R>)q7vyIq74=ysdUc(CXfjkwT-Z-lUMqzI(C=BZig)L-HFG|m58HD8eFVX5wW6SvM"
    "Mr|I=KnLhC<AOOhEWdpB5_rTOnEix(4e4wih(GGA=wl}+*sDAhpQ^V!9RVCitshyiE1Hic<{Q>2uRw-$xX;MS1HS"
    "bI+k`})<;mCnFi@BgOPPt={Rl0>`vCK2c{#@A*<#$fG5)OijlT>4CCGTZBy{9|wy|<Iz^F@}=HgG|%@Gj9yuo&yr"
    "0M`}O-a=amyyiU;qAT6Mhx=+cxrF-~V@AysSXjoQb0EbG^Gu*usK$@fW4v1i&OD*zwz8pm{ugI<e<D$UfO6aI#0b"
    "vGXfd1@8%QH9P}ev|0f2S71r<5_bu#SZzgx}i1aH|tQ8D&870K&U-3DNg&;>?(q7p(JjlyIv$KJ{~6Gw7mPcq(w#"
    "@kASts0%LH=D3DEWLTnwQ3ahv$cUN7Z!JzCk@HJE0fKQ_NMF^i3&(<?YUHH+S<aj9}DV>)({r|3<%MDMq}DNeDPv"
    "$&#$3b&a;`Ou4KvceQ0sCcW|PMqBC@V@`g`B7b$f>M<m}}TXMG4qVs25784Ep*qNft(k31+u#h(vIqE@wJuMnCe!"
    "ll&=grHL?(WXX&dbAJG@H#mTsEUkWlQ^8!_C;G&DQz)cb~&vgkGHosVg!#+qk2ZXZ5KyM;qijn6dL>I>Y}hA75oy"
    "0A(=9^Vk%&+QAeaJ=~1P59nmto3*of<jkh&iz3Q6WazG7g042Y6_ze%u=MZ(lxO$>Aq%(lxa%>Nyv!0%t`-<8THy"
    "(J?3bT;N0eD{@YC=R;88K<7$=uTFWBk#IS(U4ba<-5>K;tZyvjTTeD;%UOUt{W@n8w9VZQNRHtu^aUW(;~2*G)X8"
    "U<p6U&+OxML$fHGgOD>xeQFK9Lh^wZu6L@Llt=87-OPXzJU!lpdr^w!wSvKl$itjC4m`nxf4u_V2e5xxx{WpI6|$"
    "7hp6R?ITz@m;&cVtcc^}r=o-Q8Q?Q~U>k5w_?EN9Ds}$#(joGPAg!_7eW7gRe<z&bfE6{*u#V1su%u3<qtXDEsH?"
    "kTh-i?^=o)IH=2xD%WEaCEjph4)JhB_W5-6H?PPgB0dn^9$Mqnuw2wfv9X8%B@f(Q6SfR<dy~U>eDoOV!a(g%=m4"
    "wa8t<#jHzir;i&f8(*;$K*SAiOD-xlG;YjNZ+CMXwmk_TI1m_LL>3MB;}S+-N*-#w#_I+8;TQ<HOr?gGtBJynf?r"
    "5>LE|RMFF?I#yfkVA@NP0H83%-x#lpHoTm(dQ<P2|Mb19>iD;JS>zL;Z_d7$`ucsIntnxOe@Er&?S%nm_|YPo~~8"
    "7~_!crtO*mTo!1Ck>W2I!I_ThEs1~7%Pp>H*NGZep)uhfs5mU10jozGR)8T{Iwa|DkU#A!qBa<hFbB}bwN@kDg^a"
    "(2>;ipZWwV-fAMVU^~7(fE3#@8_5W9?w5*+uEZ$~w>9hV6;w_`vYh{Sn&6`C^-dF{Uyzzg&qAd0<j#BX`5IyIP49"
    "KJIq88Keg+H}>r9OzWh^nE1nxsB9jC+FKs|6*Ao3kTuGI%eHtzO~PkyKkJ4vdQvq6uEF{*wzSDGEY~?+d!1eNw_="
    "9q&KiV<BQR%KHV?leBMOCm|AZY=W(6SSWMh3y0*gBNZBXzf<hKBx5s|>dbQ>C%MTCPL4=x{4>S?%p(_*GG;TjMl&"
    "HJuI|eUEYliW_IU5*-tNgt?vuPYI(+3U#vfFP4==1v@)z8Q#Hrmt<<=md_pokikYz|1T}$ekh?^(MU*8D87F=PiD"
    "8IupwsZ6uiAu@?w&SjQ%1(@OgyW4!^&mJLvB*@~`7<@%%-Uq`WphRMgzZAXKGjuGJAF1Q$n;TdAW8C~=z}!J#ghF"
    "R_AzXz=#OtobfKG!bK_!OMg(iF=-^RrR8YQ>4d;8^dX<0?LxrDgkGG@eC1xWL1QJ&0w)JG`90I>PpEypRI2}%`kg"
    "k4aejNDbsKDSx3_iQO$Y;4maxq8pi(Icw_oLj6M_5K}HRjaQ+C-yNSE#Esv9y=fD?`^>(WjD<=nIwW$<K=;#vZhS"
    "FC&eh1z!Wf@)iA#=_Q!_2hdbH&gpH5xvWAZRuT~XCL89}Ul(Uo<_y-eQx%3vRJ4I;@bo2Dz2%t0kaU0Ucog#??j+"
    "3)$2yo)2H=$T?TA0Q67(&O=`Q=JBjfxNtNBk=DMO>*Suv#Rmo-bWW$Let8-A9nJ2vbL_Upn#ktZMWD{{6{&^Y^Q4"
    "_`j#MmZK1B27zlu&^s<g|<=IxZeIOyX+dT4hGbjkoGs}Ne~o=OT#5GM#pH_Bi^poRLPesc{TYeXRoU*HBX{~9)+M"
    "Q7I%cRAMd={!@07q`o1F1y-ylsCU4>;Z<R{h8^a<n6D~pNr&{IxoZ_FUejUjS__Nr0Wi{BE<oD%j&(;iH+9f=@BE"
    "%2muSNeEe$SQgW*CkT5DbZfUTGFlu;w`sDw~P<Cgbl>M4ROd*GE&(LeZ6JW&@lL7YVmxLoB4hp!lQ)2Og))v_O~i"
    "hrA5?5<8Z<qU}SttE@eUVXn!*VmC?U2#A?_Iz;q3Sw41b;N;m1hb3@|ejd=<ZspEk$%ci`%8ahPbL=w4h}d=K&Fk"
    "koCwq<vb-Z`tu<XA?L@Fbc1t^p2Ya(A){Sbz4<@)4aMW(NDMv{vA?#|yi>rJ1p_1(edcUF)&ROK*kbJbSeHhkphV"
    "9>U`bh~3sa07#(Qd_8<0@sSNS4;_bz;(p|TbK+s&ftg`d0$QvpSQ7?;54F14NfQ!w37FBH@%lU{4#lSu>YTL_T0W"
    "2qvBi;d)iHw)YPzzCv1)}ffN@~%$@xUJR~<>J!N93q4W?b{F2W)P7M!GFPq`I8&kK>WZgatzfF^~1;ytq&bhByem"
    "=wE=oF=Lmh~w7B$IPQ5ozdEbo*jCi-j_Y8*A+o1Q4t`*`yK@kYMr`8sw<#((Q-s<@gF9HlCUkaanp7YA(j;?u{Ns"
    "_4HvOXHx5sRtDIR+Y?o7#~j4ue35}lH_u%LaKjTNR!=%icBOA}l(+}X+Lq2*Za?xBqjca=q7ogAwLIOS?W&rJ2M4"
    "8P&P`=#pKB~sdWvH|2gf?v#z>;uNxebI6*aeO1kmVXfiOlOx&Bwt$AqJC7Cke!==7E46A{eP)mKUh;<cTyKT1Az8"
    "FD3}2Q|>QCL-@Ns7jxy3R+$`zJmUQ;97bAmEN(MWtRlc+;U9`f-}C#s%6Xrb+-na1>E@ne}2Aql>Gcxd<POt9EfZ"
    "Vz=S8Ejd2kM^9}MC1kyWz-<G%gDT1<7@E2cEkypjT_syFlS|h3+^O^Kq)a^c(Fde&R-LGq&WIG+dgT`%=?AU&nCa"
    "STZ!cpHfB3-J20h(15f9J!Z<Gq89bgU&DX1^t!?pVvv_3S-W!J>|m&W+~tpZ9*MKHaQ4Y_ix6);@}VT~WwtjvK7N"
    ">Gti81`2FZ<Cw~Jgv8@%gLOwj@f=+A|L_o;25dx}f=uM<>@c#%t){m2v~~}7UhW<5?lmeAxM{N4Om>bX+_u61g6T"
    "O1K$)K1#?*rrdR`fDC5DjKf@kXS#XnF?$r!>BgpzYoAVGw~81EScA~VJ|-v2wtzader^WHWbU>*yL55>5Z?9Yw(1"
    "nQ|N_OUI3BE>DUTb^@XG|dt8viF#Rjb%Y-%<q%z97Vvn>*5vPyz$UNN8-CjG=@2PpEXVxCvZk##uD;BC+Ud`(lfR"
    "^{)MM4l>lhIA$Z|h$?gQ9bSIe5hE9782(v{U_~@k)#;o)ZGa{@K2O7Jn3mgMB&901mJi_U~+|?Qm5@d0XGv(l)Xp"
    "FHRBkTDKcvHOE`QP26z2lR^-QT((K%Zch&WD@!5OmRamWx%S#t}g$0si&2%yW7|LbK6OI><0JCX={ol;+7np@$mJ"
    "&vdvbnXt5V?G_rduOXqVA4@ni^=Bg3ChtQH@IBg5P>0}=u<fd})d|OaO5VV~sUpyT221HWcAV^~$B;ekAmTZ=;o1"
    "MH&VVW(U_y7I#VNzOl#bL$LEgRtf$zMiwbSdx6)M;0rbgPVSoPNIEU*OnILgR5O<jj5M{lNHzNgkP_R>`vL{rB**"
    "EOjHh<}lr2s6i7WE8Vq^IaMVuTRxHD(93Alda9>+?<jJ1<ZqOUA8Zi=)g)h#tG4&n0aOhib|lT93V2xKW2{K4i6W"
    "%Cg=cEJ$saC44jinO(Cmc1vkjgFj0%lag_q7nwA%;C?6lb+H;4ha0Pt{DAFcg;EL9q6k{V}g=)ZUj)qqdD=x&SI1"
    "nIn9zL4I$VdpM{}P5b(|lUtKeHK`ux024nybctlN4jjBO2m$R01pKmkls87EJ_d=M=t5alYaag$;q^Gm%)1GCa#M"
    "S;Wx#XfejCk0RJu%@__b!Z+>@HT2cx<%@xtp9Y{Ml5$Q)#j|{ViKwq!R3eumArxwbSv>J*9I`-q`!Wo5iTi!nS0j"
    "6ev$^paH$Al?^>JXcEykJVqW6WTY7WokWCnZZBJ<?|m=!EVpPaVU9!*Br24#dLHO?N;?H1$k*wF4XC%JTwPAg`7T"
    "*K>Yn0(d}B??42`$||+=lc@tG!X<V$`0tofiIm;0Tw^r3bre}qyFP?{{VY|9h)4&UoCP3Wi9v$pXZAs<8S}s&8Xq"
    "6c&bdWdYja`l$ULd0mT6;nLm5)y0+j94)cgD?H;X!gs<6DuCps*YAz|*f(bvsHl)0@asEYn1)Z@Jra;jQ*|@rCOk"
    "`g+j&2p_fru7ufAtF{+p{A|Bnn@c!B3z84*2BPT8GcUEAP@9?>4WQqUMb;YW^{qeNe9uuP6iH;IS6}xGoxrQ<anc"
    "MN1@!&%ud~cyXJy=29<LRPJ?7u#wprj){(+^ik^3atUgrv*2hgJ6STMuX(zJeM;9gOxR{is&`O_GRy~a{A}`fX@%"
    "iZtL*ff^51-8R$;+$HXE}(@$e!RC`3VJ1CKP&5uD1gF%rkSJB(uDT4|(hwdwk6!GTXqJ+vl-3&MH%aMpB)cloV%P"
    "p_k^BbX}A8dZ<eIC@Rp_y~P6R{jO4$|xS<D%G5z41<4ecz*cYWE?icrzUz-kSk&%#uiz6YIqn<C0DH%3S8wwIn8="
    "#(32a+*+TS~w}I3Yrjmx>zue#$(ny>Ie|uLa0jrw~GYUjEf(&I9GaFpS19!{=)}+9pcNi{D4l-uX^utB=kwebcI-"
    "X3sXcU%m6}s=J8RJ;k@lUak=Un6@BzDa{5fSEAJ4K$2>=n^Ljd-+loAmSEFq`E87m<f!n?STMg3B408IZDRv!me`"
    "(=nbF^8vVrs&O~q8&**h+d}eLdbwsNAsK~aC}gC<q>s<~*6TXv&V5o$+eo!Vo2C$U_ys%!j{q9t*v!MPg-u>JLf="
    "sN*<Z}<#QFlfMQ&0xFvA<TT^-|SI#pmz1!c7pb`je;@2{z=Yh|bH&@}3$Qc>hB{3moIVdxs3B+&Q}+s^ccL9PtA+"
    "z3qgsY0@tZ<<bUE!s?3-2|1E5c~);FPmMFA$7)@W%Bw84(pg9SuE?}A~9&+PPK|l-$ZMSxt5lgE5%Zaxh)D^Batn"
    "W$%kYyH2||QRnkndE;e(;kzfjQ-U&tJnSMT3x;A=5eavS4X<$uLG!X0A#;FdoVpM+7y(+T+0-E8Y7NKb??dYM1Qt"
    "zjvVxRp2V!|L|WJF*&%&S3C(4L}(l@~|3&Ci0{=os%E`}Qcil1b&v&nTG+1WsgQR2ksQc#k18t}IYCGH5c$lu?RX"
    "Jcpa#QU>a&YMV6_UTUP}<>rFVHx>S!Fl}c+F^(#F1Y!}}nR)warI}e{(lYDvqwA+=_0N*Kz!C6_QGyl9BubvUOHT"
    ")mU*NUKUZ&MhW8vSHY>gFxV6s~6)mC(WrD`JTOXvE(fn<0v349x*8LV6^jYiJ;e_NDf;!$7&fu2Dwrm;{&wlCsTV"
    "aR=r{_HuUCH~ows${i2sVZ76x#^VeLx@n*<-IEJ6Z@v5kMcWj6j1cF9IfH`bsVd*E6mp9o_^9%ufJP#*^w9^1X4f"
    "O#4*W3^;tT+*2GO4d=p##lhBo@f%G7nmFUi5L?gWIOo}UL5&2iT^vV%gwQEusd>PPe0TF(z@D|E$f$y<aI9n;2y<"
    "VIRi=K;NdXW!7v*GNc(grlM!yxoDt24UPV}TbP%9YO&1};P@W12Pw3}uPnIhz#qKpo6Tg?BuOOqN>7)$=i0Dmb1g"
    "Z@5wLfLhYkxTiEYD~bjcxT_|lz4!$GUFMP^X~z;$YPn-do7!f}=aN#C93Jd>*<mUR?_qR+sx!b7F)O;CBkE$#VOd"
    "00_1VBrqv>RhxSuTBr8chI?t#=seX-vJo(|I1vgG~Gd%x@-B>S&k?LFV$IoW%UoA#Vu>ST}^Z%f%C-&!`KQtArDS"
    ">i>UyHiEJi<7r*97^+W0R}Xso|Ny<LF8w`!49H`3QBgHW~DgA#BGIwJid#5CC4e^V`(VOCE2$pN&A6J<<eHIFi~E"
    "*4EqjYfg`==@Y}%nNhu`8#o2sMxHv44m+!sI2pk$GKA4za!?ui1k5}-SaRoZw`FVjtjDx0-;gw79ju@vq$}>!ahe"
    "Lffqde`t=ae)EE9l4Sqd<v8f2ul;U&P=h8G{VrOxfz^>!c2PmzY+Vpi4@~S7(Awb`G8s+06%`e#Hk=;|n53yz7j;"
    "V|fM&E|pNRsNiIZ_{o$-S&QT)x+Z~p_Z+!GpM@J&VI##FU=B4V6=B^YGz(xf({)(5<4=jTroGrdIzCBV|10tNAqi"
    "Y%#Z790=sfRhC*u3>)p_^>!ukD%cOQ0L$M<WPzK@8%I$dln(Meoj%kwGpuOA|r6_FiQ5${%PscNo{3mkc{_sh=7{"
    "_lI+8m9}wOIeMe0#0_exH3q<w;;l|Nb^{N8&Dr3jsLenyJU5ef4sqx+Gt@_7fx(f#$Q{JsS;e|=~Jtok(l=C##r@"
    "WMXlI&PSUD}gQ(Z-;JDU5ejWem7N7~}uQFMi%emrOyVN_bk~u+#)pMhD5!OUKns@)brCFDE;S++q3_s@myUip9pd"
    "sE~-y9!r*07nRYgDsXGl@PHJ9ks%e%%|Zwv^LNHu{Y=_l-BS!MFFGsN)S@h~KJ6z8fcQ-1s<!CV%g4t$26V%oVA="
    ">bjD;yM}Pe>64UrWpO1)><oJ&DU{r%lxF3L6fR;0t0xn=o6uoK5_>TZJDg20Fq%@o1UQXF;TOM|K}7}Eu%E?v1BQ"
    "~%IEhZu)QmiB90p%}7m5hV*WePGrh1@KMzg0B>@<nP^w_np!Qi>YjcP<87;!vBqLL<2Tjw(risS9pxCA4m$ZA@eW"
    "c5~2PC%U*W%EYuByM<=ZjSBa5x`4v(`AkqxiOgUP8pk;tVK+6$3OfcDztpK;jCXDeSmpwDVq?eWj%PIZ?0^8fueO"
    "=yq5~}wy$FGZEyqaYTbGZm@gO9TX_F|O3uk-W0cf9-lE6fqnV(bicb#r8C+H6ZHp{qv-4>-LrQ3&g{xA!m}c_}tl"
    "=O(yoQga`=uk)C%oLJG!kE4Q?|fQ^x(b@o$stU59!!|DSX_vnN+?FF33Zoxnhux&bzfEHO5}kFDMwDcc{=@{rrs5"
    "$i20)J}_?S2AJu_#%wa7?TSUWI!HH6)E#7t;ha7}8?17wXncz^7?0Bxe8Hc}Mjyd8DDY}T@<?h*zG-%n^gs{tQ*P"
    "W=&F@AsG)-Xmr5y$RgHtMrxY7nF0ZrV6z+cN2&ejP(!mnh&Tmnf)v+V-VqOdh^GY~qTBl!pL%2xlZdF`p`=3#Gtb"
    "w2y4cF{-Wly7>;cHFYH%v}~@<khF6!0RfRb@iE~W-6bN)!c>GU|^I&<MNmC34btCr60Uuz|Ur;c9wL|vA8W7?tm5"
    "0dMNubE5h!V<EwI>kM=$l^9CI&U<55({kQGyQ{1cT@iwVFM8KnHiS~HhQBKH58T;HZGN`<mOxcSg5Y@>5yY6cZBl"
    "Hz8^9oDoFlvn)%Ud!(P~efn#VgLtEKfw(8S`PWD6~KeoNqGT@ee!Wt28;zhXXT?sZ_(!7B4VoPl^kxF>5kgkEyoU"
    "!z4W&Om<9d#C0Cl+Es>`8>hyx{IU!GsV!H7H#3$Rl-f_Wqzp<yK!VqkVbQz#N_BUZ)Y7r#ppS7A?BW(_IJ8i4$Ax"
    "=`6Hat*oadd*G#Tcd_9o#LHY0^FmNk~r9>MB0@H6me$^38HiXT$7v&%1FhG{B);6CxiIH}((pkP1oXPrn4Z_I;%H"
    "4jcNuF9fE08DsH-0&4VlZ&9DrBiamCGYcmSm5zJw5KdaXNuV++F>OV{Z2L_d&HEWSV0nmx%2r&XX{qvq&&&4bL`h"
    "3CXWu|4{>}A`Bw3QFnw#<Xg1fOuJqJrx=>OsV}YCQo+WY^Dvh}A^J=0~g~?wK9wbI<s=-*lNfp?j1ZG95q*KWz)_"
    "$|;zWPYm^=r6&V=p&u*=|0a^e+6R1wj!OYYeOQf8J&rgUyYnr=Ra{UH`k4E|{6$@F@qEY&#i%2<}W|juWA@>TWR}"
    "!1XrnP?biNLkxhD<9)R(<J3Ys^E$cBB3u7dQ;cz|p5p>}PuO*H^W!JuL2(Y35DIk6VjCe$eP4=CXqK?gi*?=U1LD"
    "(pzc%#o=B=`9?<FQ-iW$2OvU^t0E>@*(4l+PK@37gB$I`;w2Qt_-m*+)QOB>b9A=NF?kqn@oa4IaEjT=tBr@y`Ah"
    "82Pvb<?=lTsd1Kw{aB9=IL_OZL(z{o<9Q+fe?c|QX&KD9vmoWE?qO7wZ}c>e9d6ggvO7hQCE%iHHM;>=uvm>2a&i"
    "4*fxxJqt-YT9kS5H4tYG7pgEd1fJ%8iN6MA&WWgvVX)w_o0z-h*{aThY8od@&I5xfe6^;$YWoxh)4hdQd`gQpU?p"
    "t}-e~v05(+H{sk(<j`U+WmFkUGle8A>^3Dyz<{-S0ltIy@dx+s4@xw${9c?C<WVu>GU9tRbcTYzkX*8c$IB)+0{v"
    "h$ePPD$v{0WsU7(V_W^S<N@6V*qr~aS%m7g#=?~af)Vm|HKhb72WT{%U)3MNn}jD+i*VnD>9FivIlTcI=PdbpjKQ"
    "&xMTMLyK^f_c1V|C}g`|=X&VZ1ZUn+Y)WE3|8G&?*>_J27zJQA$(W!I54dc*%>_<+IP6fmS3^s;&{+xj<UOy_q>C"
    "d?4A6Sj7nxDH{R<88Ld8F(wlz2?G&oLiD+`UuiVLTOR5h!>g(dZPHL;KDnM<-Aa0`GjW2ysv^B;XV2ACQHQ-B`Ni"
    "tF5Su|!Ku^scXi!ep|)Bo0CmS_Pz@b8C-Hfr1Th`?*}ouQ5@-T#A)|mrM`%&B+&TGh%@&3lcjx)1d4m?y?|OYUW-"
    "uXzCg!%b;gE$niT!W|ZDx=oAL(+6t+*?@Di-soRzluD+rgzJKi^B8EJqH06eB3<{@Z~qAXR?`Q`T1-aNner=*XS1"
    "!J9K_jN;GWceJpkCMt>L8YI=W21OQ?1vC;n^ixSC*z##GY-z0r>zhm2+GssFTZiRje9BjzAk9g5(y=OJtI25CO1~"
    "Hk@H(*RmS&IE+yrFFOR8@b@x`H*5oG8QkF}#%)%om9WV_NId5XlkN2N4y%@hyOX0uSzO;?wk-n51o>bCO*n{XIa;"
    "nII;RmzmM!Px$sv~MMZ3hk=GV-5Xd;-iY8!N@&?05qA`i-&8-pEn@m5<$@);<BgKk#_@aLnoAyTgkr`=t`I05&IB"
    "rDQhj5j-$rJUE%H}V$}eFU=pq)K|vA5W<iz;s_~hn#CMw&(Np4}unAH5vog{`5h2wDEBKJ&+qtgv6o2nqufNk!om"
    "*d}i}zRUD&CHK<as_`(%j%A=p6*4*xB9Pdrb%<IQOHy{{SA3pRQNQ+0lcGB8I7prJF$p;EB^}tZ#X?QkSN7QJAE#"
    "wyuLvcN2O68%rryy$L-AAeqSy>kbTqhW~mvW6PMg+b%fM93$p@6TqP<)7dsB!S8LDjX^epLq{+%+hNe!T7$pI1SC"
    "+$nk^Nit<uJE7jDO5=~zG5rsL;h(4`STxk&V-<8oZ>+6==54TvtIwAKR+^JJ_UwQe@SUZZ)bN!_2A*wQ)1w!&7-%"
    "v|ml0nQ!JEA0s;x2HY4t0v^yd1*>+lWPlz=N6;-h>rDJiq^C2vWuH_J2|_W=emg*W6zbeZ!UuWmrK~H0?Q2XzTA4"
    "W)onj`fb38FudVVT+j{uOwrXAEp9E8rZXqGX(%V%X&ejBE!8OGb2S0r*as*<<w=l77EC+to@f;xmzhxM7Ge`rIK<"
    "esBo%h~aHk+C}UThfXtT={N$iTi(eXYJ}eHE7IXUe*0dG5rwJ6mec3c|{{y(XpW-6d=X)}mN=l?dkueO4r#7hz-_"
    "ef3su65fPDeL+oSW1Y~<*dErj*q9xwYMx15Mvy9pfQw<&XZzU+ts(w~Ngphl7`Z}Y(^CHu(}`L2@Y>RW2q)r5L_k"
    "*oZ4=Qes2~sir-2oo=uzkX!xr}+ZEmiRizTkZjp$IkS$3r8n=!kkDkfV^CvNMIN(5#iDRaIK{WlfP*WrIc)xT4J%"
    "&J<^=juf_v-g#b^Q|koDBT%UlmK}?V?rK2#YG+5tFBdmI8!#7D{nZvnkdlI9PBNvW_fzy@}<#&%IYe;@)wDUG}6~"
    "*{9K?nzED&4iIj_xvobSZe1%UY#~tQ%FY<debKWlx>ywNTi^H(c)#AY|yaW~DIktKHf!zKe)hibw#d#|Q3yEu?#$"
    "aVVejzk23;dadPgjJznfwTyUI)P#vIk8Q*8K5(TqQctS*vR<aP%79j8Cq!)N5#CMk^=OkPU@;sG(zYV^c9W!W<Fm"
    "Nx6n?18uPe9q-k8i?03c&9}vX7@71-FIVOePTAl(8akm_#P(86z!H3XGD(J(L%pkFS*p>fB-iU)jC;dH-;oY#opb"
    "f}40ldWepsZs16&+VE<v5LJeke0>`mF>YqHFz8B4&O1{xyiI^DL>y6*oOgTK>bkTtL#nG6}UBj4JpW!8ohbjx9tf"
    "e59Hi=!qvYxnTr#s1MNf=Bh(T{MsA`QA$qCXUu@Z7m_&-ls6{h<2XTmoPAtk)&wHS<?tWK<kV&t`}!LqN`9r0$he"
    "lQVH}24Pmk<hgX#5G+dO345nb89?fritX*w69I3-<5|Qw2bBA~w_gnO%<cpjaw_gvkCt`PV+L{2mXk)*jDDL)5IJ"
    "*4p4n<7ls9P+paVi0cp+A~qN#Q2NBr}B8Srq*i{^wypEc)SK=hfcv>z&=b?wg~Rj^MnZw<fTI<cAds80oOLF7aiz"
    "3yv5Q$=L6nmN}^qDVBSk&QnPnOZgn6tSh8SxoX1dyF0EIJ-Hjs>~4B@pW|*pC(LKApI;BbU3l>B^TUHZ`r~--;N)"
    "(sR(RDY<E}wGU2<(QM;>?Nr<y{x)M@TSW$BEbIYA9BemK`W5r0>~35bhnO?n=e*-I7-J{GBz8xKG5FLZO4Z&yyW("
    "@2D%i1q*WnbDO1Z%mQqUDdgJwD<erZ+p-0!v6X=`H=TJ?KGRBWfoQw7OWU{HrGgv?kq`+c4V3rnb8#qsOk=>5roX"
    "$+DW3aKyaOody~EeNR@m<6E%NZu_3yWu_eFZGRB#QijZ|rA!EVgi0O7_Zfx2}8Nb1B7?uW?rNDdfIr_h5{hHUK2{"
    "`M!q|pj~5-jAB7J(JA>V5|<1k-*uCVnLSHCy~gqv=^Im%K&^T+wiyAF8VDk`9-%JfqcBf(dSb)o@esq*kjCl=x24"
    "SS~-tjrkFIk978B&k;6p!;@qQy4aZm)i{cXJ6g=n5t*Ayvw?308ncYo{w0;k(qA{?wktVpL!^X=R)k@>cIj3kbgV"
    "<fufor2!vmcZiwfWQc04C4@-Au57RH;hgk=u|cA?vyWxPWvqmd;$^!|9(nVJjqD?lUBuIAChpLLQH%JQ8MmgVlhY"
    "cdoGp8sxArQl=JBAnFieVS^^q;T>_TVZU)&&xrWZY|uGnlYq%xD8X=#Q7W^B*=YU?(d#75b@#pVIp)zYF5R19jfH"
    "gZl+{xl~4I6GQ0F!&X;Mm4}u()M@E=eT^VP~X_A^=oi8JrfH)Qfm4(ruXdKP;%a@N=@KI9hT#0pe=U^A~ZxC5~7="
    "1D%E_$Ai#WdfsfBw*pPy)oUeAYR5^YUfNhSQQh=q}^CZ2ur>fM~q){I8%j9lbd?*gyCM{`&dl;VufxO%EaU%jTyw"
    "GH{Bj+;#50Ir#11@Q;JLk?p_(H5xPx_4VGta~|Tc{B@HdF1@_!Z>p7H;njW_*$shZ3bwi88?xCb=TKm`tTuwcSap"
    "uWsLJfBGzf@X5`f&eoIi(<Ct91B{7a<MwcJj3v7k4@rC}9u((9-%bZ=**FIvwsc|AE&05rwCyr5x}i<t|PCrW!+H"
    "O;Z9JpjC2Zdj@Zf0EZ!3{F`wyh4Z{;3?8F&Uky1Y?zn5yfI!3hsB_AR=_{w^RC()?%r*x{h^ZDKqqjSR3Z=lTc>J"
    "s2p@Bn_`2dOF}?&hNTZ4V5vB5KlRxhVSvA6p#`JhG;mfQ|cixukXIBEY?D}hd{4sg*=z&SWG*_&w2gRC2$3{a?QQ"
    "Dml3DZh<H!qYnG3Gu7d7hokX7fvMi|Pd}+&yL}Fn<?)h(xW#4ita>CW12WVPphIfG*uQ9VQr2<cB(8f^;cv?oiAq"
    "SnwPtyj*qF4+PS+w_`gDTmw_96D?@TS~QN7m$VhEPMUZmx|t+VrN-Yt0wiLL^G`sVMcx@@pBnl>SH)Ein_qYVRm0"
    "Zt^%8DT4Pg&N0LSwkM);kkRR#6-f<au$@*_poP#5B{BNFqGdI1t?vV3yRBGgRFLz42x(LbvOBI>Mk0IiuCHY?Nk9"
    "5=Ee;sj#L)#xVCsK_;qutB8Ewvud#wb%9@4X3P&3tdX}D14fj!nXbR?Kp^@6_e>*)4XO}u4~v#gxM0R*A=_Wb@~P"
    "JmPVT4$>T@^!>S5bG`eAQ5T(thODI%BkhRgSvi?Vun);x#k0u@*%;7kvg0~q$;Y|huxOYLGgV$uU0#V}gS+6KX^h"
    "(O&Q=(lZqa3r_igI*w=oj{=!sPK(YMVDFyQ%q-Pc1CsJX-?^s{)m>m`_F?bk!di!u~wRx!?`J7S*n8mtuJ$<lHqq"
    ";=%)O4-ipCaHGKQsZy{@F|@D@cogK3+74l@i?KII0&O&+9`tjLft<7M1>BW2-4uO;(!xN3b?wT@(0kXuez6obW(3"
    ";>gX0v92QOG07<_+*kn*>L4vRiEpG<~kGAHmMrT^}7Fo+ZB3k#*2uz|Q&+q4;?CEkxTIgfnzE~|Kk)gt?Z*+Uq#N"
    "J!Mx&QK@Khlt4xa^^+RhYQiGe^5o>YGDF&!$II0bN;1l<;K?L)}u6enkElnSN{W3?>n&9HMU6$0-{R<x=4P+T7kA"
    "oV9=^H`p_?Cj62?)d~g#CSjmTOf~9p6sR~do2x6*>?<zYD)3N9C8Rv6yN#MpSJFr^+$j2!3e|BP<fK6s7t-ZT*?L"
    "G=8i$sWQNO)Jl)B6X%?}1=&^w;jm;ct5f!Ly{@0h6Mg;6F$~vQBi9c}`<T&HhH4H1f;V-zLSFV7<_i*1~HczwYn{"
    "*m&r^zJ7OyeOd6G6MrqGF&a$+kfQ-f9d}1MbbaezG1#b49WzJQXMI5h8iKenEJ;knYXZK4znkH8C4Irx1i3iujlY"
    "%t5Y}v2Z+<NplZuR)*HX?%ziYVT#4cHQZwHT(XU_D)=htY`PBmov0`q0V_MyR_&DNM|mz&3hGY5e2_=AOb2-$eUj"
    "lM=ixzz88imf0I7<L&qx9mLHG}xdW+};$uYNt-+hPuRa<{dcL9udcr?f}#BJ9>Lm-|y^hZy@&jVKzGJXGxdBv$p-"
    "4s$nDpUgL{A8_q9i_5HMzC*DEQE^$;iX}zc_nJ_RRoRmFFn)OCkP(XV5*5;Oykz`2MAH_rA8FDCqj}Wur&H7uOPr"
    "0N4LbaUZ>W_1*F6xdPo&l+9#!u{0ofF{n#c-G@NPgJd2xt7vz6K!sWuvOk;dbRmewP<u#5deW7xQGkI4hS8jHWWe"
    "_@tTE<%8Lr!Qzfq4p3|HVkq^vL_-+fG-dJ;7M!ak)eiKCAHy#sB;9H4dJ25;q@hQ_E^F#9oXMjwQp~cA>~vGzaun"
    "5$5!?)Yu$@#C#9b5JDeLsiEOBK8G<QY2YogC_OMQc$>D0duR9@=@(pZERX4m6w*UeJ?_sre-B!D4qPWX*V`;MSy-"
    "k{y-8B6AK%XQkDtDikH&n7=uak!yfY#DPC@hC#5apcG7s;@UDsbsTuhieT~r^}+F>C8}+MNOizJ(2>inJ~&{QKAM"
    "y8Pd>4AB`ZLM!N+Je6wYUVcxK02S;A&rn~H3OnN9zIEHOdU;LbSI<CbKH1Uoo^xG6p>oszQxrxJsu?G8;27n&aj!"
    "4&$8|>Ykk3KmVPKgW3!rO<79^D9kU!Z{{MjEp|-n;3-?vldi#RLqP=McP_-qM}V_HVkVubmsd^V$A=?OC9)E4YLR"
    "6yA0LvVwkj9fbPJF^!K(egx%rvY7Sq&SN>;*f(+s`Mp^gL%A4@G9+{7GbTQe3<%FroPjF<nht_dvG0dLGcW{&WlN"
    "V!hvo8&Ji48HHh*7N%tLkws-;7%ya0WOq|st?!ZoR@WP|3Q?kSe;;-tT{V(m2qt-iz6LJ_90m(4^a{mgY1ov*Gpe"
    ")`Nu+WR(E^^}j*w%%#HI=a<idCGi5n5>=8`X$JXE&aADlZ+MRvoOd3TyPIPMh)Nm!ppX{jfAvN*EaGJ4%S^%3+I?"
    "OHpWs<J(gZrSEaBEF`1CXDNPoo*02WAbO?7>|2&`F78;kKaN{VqwfMF_XJ!712eV7?htCT%?GR>Tt-<7m@UU!NBO"
    "1#CuhbGkuReiaRC^x|m+1RlU<p$cc+HFDGlmuJksS^-_Y(p(eK+3SIoWx6_={x>7~}ohn~mRh4)$NZ-0{RY{IHcK"
    "PvE}~4cC?SyT2ap9=_Z;*;6@F_&t7X!$Y91-`@-$IzBnt`Qzukqocp_Q^)gJb_o{^D`Ra^@3$U5#HT!1PY21fVHQ"
    "WFHSwR&Lcz4`ih;-j{R4Lg{&ZFl?6{995Ww)-cSMjw%MXhH2(}n25G)MbfrV`cn555V*<fz__FtvlYuro#bUIg{)"
    "2>B2MFUQmgN~1vmWOOb_8X^00H2wC#+HMdC7F=hca{U^BVRB(4GE<}DikOxH6?83a{{~fY&SPaBr^dzc-y7iHP&E"
    "62lHe|@hK%~JhCabzoP3;ixW3!0I|AVH!3l*R-KP!HMz8^5Dn+u9a7ZcBU2_?9*B#^p<|#hg$Cg3hnt&UuT0e!k="
    "U`M#2#vdX!9C{<N?0d)l}PDS_g)@uI?viEj)@}H@`~QQ!xKEYsJ+kFWki*HvWJ1-o>wNE87?US2XFI4|Xa$kfv$J"
    "sb>x)v}H<w0n$!y!cPcWfF{QBSav9r;eWq-z4l96vP_b5&+puO9u3xGYd_Xrdp*C4%YJSs)~7c4W^m9QcVu=2H+~"
    ")Md7f`ha|?Ce>SLmU-}_h>@~PnAnWJQ20IUHTfudVF$-rjK_zKpqaG@F;Tvw`9;92|NdBhj24Iyb$+r^0@$+0v~u"
    "4CbH69xx=+7ze*MmmjgB_Q@<G#?%-s>4NJ2b*vFQCI)k=+*#cMg_aM!p%1{4fPbdLmUx0@oOq8_3enR?W3dP!(Sk"
    "DOvg#ZI@BuO&@sWPyD?SBR-Y$LG2FZdu9EX$I)52%Y{1UI?hPU4PheN@O3nV2%2865tA2Z)1#{KB0u&O2q!_C@84"
    "<leQ5l32R6o8M>(nlb3gC@i<kwA8%D6l$ST)XLtV^EN_FlwjFf32a9@0?SP-bM{i68Z7Cz6QF)rUZM#yTZH7?|Bk"
    "+qfNW1D}v!5-64nE^VfMU<?$fb4qUK7G2ne^@}aBg9u4T4rVXbHR{Mn>^goAEr=BToKdYQ-D(JT!monPi$Z)Aq^l"
    "mLs)h=t)6t^4?B5R@=aqU)G%1k#*d}8_@Fhlf)V<dyZer@aO<rRVIhnRx@w1t>NcbCKKu)LQWqn(G-<HR_U6X6g>"
    "FvXzo|$e;<%?YU#m`uou=unvP^4sd!rslRqv3GOT8<{sHd8+*WW#1~4#iWIH2gk`oSIx%-@qaAe=duK4f^Pb?I3^"
    "*^%z&u*5k+6US&y5wEV!GgUXXu+;QdM=rMJ-9U0lt6fcjre>e@35vk|SN$o0=ood{*&_`gy9BXG7_>V>fl<^j1W?"
    "*Bkfq<6XEG7bUq)NqQ=26W{v?$WMW4aYrP2DYqWw=6RQ2RykE?Ul_RQiP+Q=kCUs9-s?lB0HPgsW2Ry-Qr)O^x^R"
    "pzh<gkaMasf*th!sR7XLLFG=*I`5uBmIF-?W;*-P0f46H+VO#LxxB}_iJuG%>dY}f84<LDBpHi~+j4Hh4Ya5tp`d"
    "RkpArRkEiss;f-G7ccI=c~agB{HXA%Oz)z`d82(Xk!VC7INS}sQ;_0r{X!jmV#lI07I)SjmExlUF`WU;xL-<wQPx"
    "T8{|liv-h1~ayS-{4=D%jt*_dESTy=}AXCDj2>D(0u@!vhFgpDB6)Q@)J(tH<FFddL|9nt`vgk-)~TRQ~x;wS?j~"
    "S@n{Bm;R-N(6%N4y!XFU#K-_eg!4Fe{oimT>PBLNuz2ne#)qt?brw&A_llo^J$>uZc&vP*e++;DHwc?!z#k%tIi0"
    "lHT+Duz-z%`++I!lS_ttp~TdZl^~pX9F-sA23}Gv|qS!#O^>Yv8Q1qFn=Sx&;C2V3>we5dPj03|SvTSb7#l59TK|"
    "=TR-yv_n(T*b2|qcY!ACDKX*{QxZy4YhmutzPD*=l8)Y$ks$3^Cz$#;@PF!?m;P}KUaQd(92^iN$n1nii18VCov~"
    "(w-S&|+PSQK9J7>2C@(wd8;YsEMJ^A_d3v)<;tbaKHot)f2TpdAd?v`sBntP*`8TNX|CryJs2VG`<Q4xv^UI&=_N"
    "w|3Q(&e24y$`hUu=+JjMZm1-4t+~9{p>ZHq!-!5&3nh@)R6&xgR~swxl?ROcdSpoe+Yc)MIW%8`$6<Ux^a)5^*H+"
    "D2d1<qPk`?4`||rg;OAiT>G&SjysuXqHz5Ou@uM)vL~n2qvS~a50oAqU%j(uCv@}pXpeA((=x5#cc^MoB9JcJ3s}"
    "IQ=b8=nG(9G@}f!iQAqpSl?DL&`0eC#NLGd`wsj%#NZmufuIt0kNTfLu8Trh*B0B4zFY{s{%$DSGE{29RY2<cbxM"
    "k+wv6tri_l6NI;e05h+ABDRUyR3Ho(ix&!GlLE>cffi4C?q&Wvc#!ZOZW&MuemXrpqG9#zaoft3WLVh9;MwHTl4N"
    "RR3+oAX4%gj&Y(JXcWJ*8h(qZ;j(%%zxW42r*i{hOkYxEt6Zye+p?MNEf?BNi~RJv$jShEu50Mg1z!tjQFp%f|j;"
    "tHBEARjv)Y>}cz7tAc3oV>tsgkIomszg4B0@ZRBYKb@2iI17@6c5xjb!F}3Bd3pwS=h(5dr*_qVapqDuycd6;8#h"
    "`IIARO*&iGPi(Km&<qW2dIOsYUMxaC9Kz<o|Dp4f0b<5$0dpDPbLv-x#W0=mCpO%hJUQ7BI`0xazzk6>4WegEBVQ"
    "Q(GOVw1SM;CTDs4-viDcJjv-`D1=^K3M!B0B8K%u&5JMcZF&t3%xMysc=5jeqrTSFM8e&j!qetr`|PV$C4#SA$w;"
    "P#KM;XZ9eHMK_E|;Tt@A0fXn4)s8Chs?9uBF&C)(V+ac`xWVwh-4%N==mx;8Fq<q(UC+`r`Cu4LNkWl!A-$+Eeou"
    "=i9aAE2I<W*aRE+x#nV<M5a<9VLg}72h<egtop%^s{dxuxK6g9buKS3Dhs8~+M_|9w&z&?}?jPJjY!xk^0%AA2zT"
    "lO8{R10bl1U{C^&Po_ke`|-w**zLM)Ts=YEmZ^V;2#mn);Q`hdUJ3HXB7$2?*6f}TKL95z-s~`j9fh^j6p)3Oyi6"
    "O)G~fWr={63ET?Ecyg>n7i3kwV5@Gzs0E;9FtRarT30_hAq6aznBzt_8>dti~okzuFLbiD&H(uz-7GUPkS(87MqS"
    "Tj}Ld7Mh`71+a)~NC98G#%#Ozit6!+|cQb9NS4_B#|H^t^1bm(5+5-UR<mP$cBG_aQ*Pq$DP|{`spww~Y&;NTg36"
    "3Pe^hp0|3`f0)IAH>>>}5b!Hy0sO`2pSZS50r;;z=OF&G@y#z6z`=YYs?rQWG8oy<owx>O2g25DpvnBro3j`n2Cb"
    "FCs|Wh6dRGW-)E{yTh{3Avx7XQ}A)<Ahph03ooO2s#6V?G84TYchga+@A!Hef6$a%(~XT!f3r>g*+QM?l-C-w8Oh"
    "Zt`a_`{P3-M(-dVdI{&(M)UwO6Nj-?41iWua&ugYp!Y#gYpfstR(9~52^@R?5My;P*Uf|7_p=3AcA9*pAnnO8JLw"
    "gKS_U-=97y|2jCdzA%tM0MxTTkGNd60sFDZmTBoSDXxnV@oQCmVh1)b_ONn0@1L|rvK{PpV@(s9j3@l><NqmVQ-%"
    "TBp=_lC1nsBB77~1au&+hxOYgXusXm5)3B1TxmHodx<XIJR$5CjyZbfxdP$f_X3>*D8dO7+7nSLs;Xi);GDIbfq{"
    "i!%&b)Nu)<#z*d;uz<A9{o=Y$923I9mlPI4KR7bv?W6nZMrz^!0WMI#Zz_96rUydw5&zKJ23D;DhaM}K(JjdWZLN"
    "w;=aZaqcvA>*UJ&HzD4WAyP{0BWBEVcmWbluUSRab=#fwn8kXw~1ArMB9&8f=eKN$Y`3Yx#Ti!SLv0i()oKL{&lQ"
    "56SD{r5R2WMd2w=-xxWW&#s`a@3O6{D>aOU|_JTb;hsX2_gD;TPZwNcLPyU0GvIHghiQDG7AFBC<tA2S9gN5s{mh"
    "E>r<A|`&e+E>Etbzi&1go8^6PmPQEGl5L-aF{*8Q0${GHkwNV#hzCh=o*2((5BgkJ;``{h;K6SSf+j#b+6J1ka5I"
    "y1Z(C!-lO-Gmd?erj<1o}W^)s9m+oeG)+#OuNHt+u?{)y3pJ<j<AHN&rY%rH)ta*O&wjFOY3Ga-a6A2%Ikl0Vq-+"
    "Er!3=!&Psx8t6DL11X~f`UNFCj;%VuM*h(^ga!lb&tJCVY?|FtJ}KDCb;%c$dDmP*PQ)CB-3u=F$Nfj#&|>|#<6>"
    "^80R)7fqZEI*Aln(xSny?xkioz1UCaZBf3H_`Q1u$HzUAs3h@>~L0t3`QEfr-wy~cgFh4vJD4-?AE0qd>drq|Yq<"
    "Q$qSWs-;>plV@|YQioI3I%YL%Q))y`{*d_HtJb41n36+p_m?xreh&Hz=7jZ4my{-qDZ(v(16Cof7U@nW6aMS(g*s"
    "SPN@Xct<BgO=+OS*!XjL9L}W#!2_w|(z1-i`m5W?C=mC+Fj~{TJ)dx<3rDu-3!$ArxZf;VT7G#QOT~K0?RR%9g$L"
    "VYVQrHwDep1>hy)v6{mN*391P&9(IG$$UYw4puri1_^2uDyaUd_`RKo&>Fg(IM10Pd4ds!ooImKo7uNg<W_EGMT>"
    "i;94&B4l-Cz!A-mj^oj(niWLl8T4H(vNIsHi5H!l^mqJY__WIC!TE!4qSxmuoD%#E1&r_<7G7LAiXWhh*6N}3$*r"
    "@-+fVCmleSr1h`QEVD43#LGBuIJN*;*@4O2MkFc3M{pj@t#+4LYd=(eb@491$iPjlqh392Iv#R(jMN^V5(TUWdU="
    ">&?8Nah3U2`e?ydTeR}o)bdqw%6?~0b-lcR{`I2!3d=!DPw#e8rMNcL)rO~eA9{#^we=TSIamZgMQ@=8^y~O`%D8"
    "fHE%SwKlgR2yvQ+qjXk9&!E7AyqhXznYSkNW8jegknlgpyKnjI}QUdHKiM!2MpN7V&W)n+ewHhfs+%V48gMoTC1S"
    "G52YY7tePY7O_k5Gdkj9}<4q1sZlGOkSV@WGN?ykf8<U*MBe`L5O2cJKuTPm&rwFVx|$o>6j#t|wTk-I-4&=r+XX"
    "j3wg1!y*l!-LXK=Is=RA*><DJ#hHOx_<Kt)L_MVs(w{C5TA3efddgMv6W}7CbPpcVO%Z^U$|L)kpmfn+8%MlRbh2"
    "h$J6d6)(Fo8cuTd0M`vL=5r74MF!Bdu+<x+X2t=?qLV2H^_!_Qih>sCvH6r4cR&p!+|(A=;Q?eD$XQ!P}}Aho0$x"
    "5yFFJ%??hRdcJ@Uf72&4lzqJ^{kMwtyvANzq?+97X<rNaxZn#+mQGuXTW(GUMqX6V@5HQ89ygcYDTm_B4-uFl{)^"
    "aX#s~QB)Mdlmy%4zSkmg=Obf%Fr4m$WY3KnNMxG`T8fU;V3LsXDf~E%zbsm75g*T%cmn8wYJ+$gu0a|WIk`;Y~2{"
    "twaYPXdP$srot;Wre+aaJQZ1|o{}5@Gt%4f=BJ^d%2R17ln&xl1NIOIK(bRu2RERD+Jd#IJMQybL7)O0M7@x0)#8"
    "ki*t_y=&OIwOVXf;|g>t$TmFsB+94@R{Bua&*t>N_4B`K^S~-T&e|87vj^)^#47IC+IJ)aV|4`@<GUQR@@C%qY|V"
    "-{MteF&FI{rhNbKhS5Tv4Aa2gNxYU;>Y{Wt1u%8j{K?Q*cpQ%4-5h2BV`@(4?K!N!+{bgNcrS6cs;1oM^qwHp9jQ"
    "uA(QX4$i460~UQ`Imn*8x!Kn)~g+S^VnWo36_te$5y)`QVRAg`ggP{mCS0kAyZvqj~#9+>XU%yRrM#!RJ3~T0!E5"
    "Kqwq+KEa3yB<M3Phwl93v1G(24k8D7988CeKM(vDokW6b?r!Sn=J!eYa=%>x4dd`Nm@!$=wT3)>|!^$6#1@`MEnj"
    "(5N){YgW_3rCwYIQnYV9mL*mL<XRdrqP<fL}7~D#W{aQ*dK>L7ctmUDI>oJLACM&UW`WRDUlUGTx;IR&6~BAD<1R"
    "EurwCxHQ(^2Y%jdSjLb2g93YriHUXJmS;?*kMPFgVY0KrD!u_pk96j@DaOhki@psL!C0qKzYwh!hp&$Icd6X9KPF"
    "87s4K#4C#Qyk&@GDP4_C8MADopM2q>>hj-`P*$FEn(Adr%b!-g1#>gQG^jQWY8z#Kk)hJp#RRw4^7aBZF}eS#OX@"
    "nDzik=80}y$a^4U+i!1;YMwj9<$0d9{47fRbt!-RJ&?xgUeIlq!@m%<3B}-GzMSh&(WrKx-;Q)S62wP%!VhUVupr"
    "5JJ20i%#3ZlQ1pwe-4s<($vF=ilU7@gbVN&y0jZUWW0{srdmnqM`*x_>2Qfk$9xDku3inVqtUZ_^5z;BBoi-GJw*"
    "d*yq>*1ze2;6a&<m?SLm+z44Bso}3|>v)AiUHtgOFllf6+;@<2WQT;I-|XwJIwuOY5HyN_t9K2Qxp|G-%9#K_7Rs"
    "7O%!?dKuV=5(G5#BH-)K<*FIbi({=58CqFHWWzmv%sq>1$^72&=&v1A^C<#rR(5V>Oy(ESwi`34!6+fK;dZW6cJy"
    "^wx+TD?;C3)O%QCoDLQcbT(^93WDaYN+?A|`wmf}(op{<WiqLtY2Qg(`zI`V;{SIX;rR@Le42)Q<4u3_W<$?5if*"
    "!q9JDxSqUEb3n7j&+PFGmZ{V@DB%4zr}h~)*`SD^=kkL>K6s1nvbn$w#zi1*b6~NDo0@A{1g9E6r|(8CwKi2cJhO"
    "#Nk^fvS1Vf)i}uNLYP^89PoFM>2v0hQn!O5Tbdf1>7Zb}NJ3W1ui5*ML18SfgOhh5CT;k3}oNWjK14dVk_|lc~Ft"
    "W?4@3U?!*YWPo;V-+#za_tJ@152Kb$u$Y(aP=p--E+>5%esZmWI7)4hR4qx~eVIwwq$C!vD`0T)WIsC?j-5eks2+"
    "95}msm_-I~{d4fe(TVqhs)fwuoWt#a20pCXi>UI7C5dMHaS-VI;|6QK{U1&q_3_qSVD&XpOD)v5wuz&}?+N8Hp;M"
    "szACM#JV8?%E2zfz@*_*=Fzxxzu>F~}Km?%mQ06l}pC)x0+1AmTihaQY^PQ4jOw^p53ry0bC&Iw&)2KXn-3pg0KV"
    "ga!+B_QZc%Xl#YaYLt;80nl7t6iM$dg!P;JR2ajs{7OeqXt~f%PAF#*5l((YgaPjj=LynROh?<#seik(_cr7F1%+"
    "$biqkLtpTuCbGPy-I_q`4xH6+U*7&}GQd(Ys=Ba0eXh&($f9et%l9xU(t@vi``Lu6SOZF3V#d%2RCQ)>w_TdFQzP"
    "0H*0zHJwh!y4Ba6Py<lE*YW=ecHwZ2-qJ`P=J5EXUwJ1y$$`n1>tcZwaP+fHjDua8gYPBb=}JTh5a)$LipN1P~Xx"
    "$SQX&d;OUt76dHb@{G*x#d3U=E!=xs7z*rFuXK%sK#6en_45*>B;X$0I~#C_%!76+>vwt-K)cl>SLbD<ertSTm^v"
    "Ff&w3bsep_uWG$*y~h8}i-@T6IL8drDIewtzaHmfDm0=rq1F(V#P)&;n?#j2?{H9677Sec%-o(aH7fD7rgkToK;D"
    "MS`RheFkf*U7RV`j5M{@n)Xj&0l6_T)`rw+dc#)*xr4kuKloNcU7#`_CsC{-|_BW)gWC<AivTyDO8-<pBc`RQHxf"
    "WcHC`=Kb}qUD@2jQazHe@nkZg4B!hx2oRiCWnN@L`QR!lu=>{Vg+lMWV`;X&WcE|f;H(e^DarD>2y#t?QZUfaG4i"
    "BPRrAiFPeTl9o!W#E!%n4JNU%Z{kZJkKRK^s4bJWMsm)iA?hH`Zgq0#`n0v9kodm@D51IyqOpWV55{!wBcuVP+C*"
    "{vF%QHV(4N*kN?t+DsugWRD0}f|>~nWSn235(5gz4N1>PDp%8+%)|e*<P>#yb*y1Bxwv@(qw9P!<^&_rU;0U=h(B"
    "BUL~VJvE3nX-ln3a2U~2Op1HmDkkFFaYl8N?01<XkqhuET%99H*4LlzP9i6k8}R|z3W0B0SVK~(nGMUJwiRA(IO4"
    "|_L&lRErWUk+Oc+gFsqIx;~9)8W;RHIs-nC0DjtT;)1J`gTu!Q*cNBZ=muF5?m~6{}J0MJXcP*5tV8*u|$?tMJIn"
    "@*<R`mh_li!peNN)ESv;?+*d8O^njLlDY>jg0WC`J;OEC$fGGhGXiCsP(?Yx$XqTkIxi^SLEapu#LO-~a7Q;cbKg"
    "Zz62}(7${=wy*YU;Go2h|W8snS;H<eR~pGdkxq$<`FSQLN3WRl^By8^^B?4yaI#WUqBGJ)kr03)y{#5Ekk~A_zfA"
    "?F!A>+$V5=TBsJyU<<9&``V=S2~@;JZ2BIDu?0*d+tB>^<yK5K!r{hCBO3`-f{INik+k05s6j4p<k~=S9@6sT6{W"
    "-4Zd~plZ(Omj(l_oy$iq8qkg(B*KL_rvSETB{27cGX@|16STW4Ve{K49ImyAZcA{U}Q$PvSIP?qj(HKulQ<c=7P5"
    "`3re4HMQ=jh=!GG&h1OUZb?#s-jC4mMDE-NYNKkDF%{X5U5AVZ7+a@>)MABV;$WhKfa+PH9}1JBzO`gNZziw_8EM"
    "0`j9gg!a6voI>*Z4(Glp5_l`Ht5kDJ!aTOWN8vM}w`6<vAv}xgEaFgug&<jXe1s<e_pgYpa5-W2<Bj@BSqb=yxwA"
    "#R`t{Uc^V<?d{Co+~;apn9T&?a!$M3B4joV+QNa$QXGQOA2sJy54!o0b?+quN%~^S;MODmKP;kP$;l$C(4T&PiWc"
    "NAr>vR(^pOlvjYkiovp-fr2;$sd6RZVi;|Xn{re+Deuu_lyCs+Ik5!atMV@jJd}wrVD>f15nfHjmANUcxHw3^Jo}"
    "VqZ|HKPv|O7OPYvg#xF+IIB4gH21JJrvE&ubOI+A;@Mm!QAnij((@4NH?T|iroaPzrl5JlXUjOiku=$AcbM-!=yD"
    "*~Nca_<4b`i5Y<8*kRg#vtJY7;Sl1F0z}35Kn!G5A0kf<6a^PA$(+ax%v$$)xQ->WBwxqJ}wDyvAmP;f)a28wFe_"
    "ifA_&86l;J~iXe7JV)0PFfwOSN0|OXUKW3@RLyM?dn#@cr{P0=eHnZX3O+M{BhXR*EgdxExq^sLqYHyRH&f8kP-O"
    "dU#U8^h(N6uJ3ha;Gs;k3DCZpP|qY93`>?u*l>)|oG>Q&fE3REhBg`7Sx${oCu^lTe`VLqKtw)@()c*;;ryYhdYM"
    "faUPu_5OY=m_qO)TA>QpVh+^kAS*=Z=IEpuOx3uGQ?Vl28-Y^bgm<flR0@YEZ4+J=nXD$X5yL-*)!L}kIWoAxUx8"
    "AVc<>IYA9ZV|l_qw+(gy886Kd>4&sUyql>(r+kPKKo`oZd_T#qA%3B#>TxW+8iepIC0`)W~5^Kd{8X6YkfgdgQ)E"
    "`_|035OP9za->~@s6li5yqlu_yZ|2s1BzR)!60qYMxRxipqzK(3UKLkH80U(n7560SWozzHJP?wNux0Ez)LZTD=4"
    "icC*zx)og9;Av?M@p`h!QNwpI+U|%{J8oZb5Gcmr1cF6q!VoQ#|@=FM$ODhl$Y8p`sM4+q8sx4<1Bn+gXcxx6|!b"
    "=eDZRt#H5Fzz98xWWRfS(wk0(AJn4T!ntfUPhf&LxJdIPKYWK_aYJHt0XSyzeVsz?K&cxw;w}mHANx{|7O7Wl&nN"
    "9_La91wx$EB&z$DIo9Vx1QZjT+70r>)mhi;$|(=DrGiRmxj_Pn8pOhhd%|C~AH?ZoFjZt(u8}LUENhZQDt%}f;Or"
    "Z#8q!2Cgq#7jF@Y3aG^v*@f`+Na9FgWJ@q&Xbv%3@JYyjo6->=hUscnU81vUdouQGRSzdrrx@Oba^w*-WWj}2MAD"
    "V$*CmoDeYvEogJWt){M2alJ7=q8;m38u{?EygHq94*!U!^(c=pr-2g&(%V}Sq-HZ0V)*#>GdF2fKp`Cr(o`0L$Tz"
    "q!NXXN=J|!%z;CDNNNpn32$tYT7if=N%$FH?-Ez7Bxk5@|8;Gf-1ZwI1Im)N7p9%<}#sDh>Ugzu&#@2wMRcJxt8a"
    "{ALrW08Ob>j-cWubzPq>I5wPY!>DdzOh#jVhf+8ZQ(v)vQ(^;U|X=9vvSZ9iHr-C`y&kD8;0Z`KiZ_?i5i?!7sZ9"
    "a_xy4pw);O&X<bb72SV{4#))?s3Y~|8-UO=#Xw<T&YGf*r6e#q)!{x~>0w_q8w6<r*L-X>q=pB8i@>KSPUn4|-4a"
    "N?`lEzLU}ldL;~nKQMImbG6wPBG`az*&7zhQQMyEe*pHd~p+w>g-jxWH66D?<bwa>4YH-N{#oWgY=k#q9;CS`GZ9"
    "s^y0sh)n}LY&hQoFhUY3>`wv6bl(GCU-GF?vw1q(iBDRUa09wr+3sNXpq3MXyuW7kr4kBbH%UsN;^Y>o&kMZWX<%"
    "1-G!l_Y`@y2p)IcG#qtWn_}?l5pDw|edhSPFV|(XHwS#Stmr%Y?agG%C2DYcD3<hb%jZATz<Ozr2ogZ5JnqB1FPv"
    "8dUT*v^}qFND{@g7)6z=1)Mry%;Owo=*J_M|_tru>PXZA{mv7=JatZ>LK5TTZfm^nC%xB=8BPnL<~oVvZWsOxKuH"
    "o4BJ9$4}HopK&Q2+#qU^_04m2Do*Ya-XG_*VbVDuPst;Aj^8~Y8hk<&2Z?w2v<oZwG5HddsE{rIBt)J+!sLlIX$t"
    "ZNOI^n_h9ehp#~Gi5w*pNi%%5V3Vus@>0k$R{q71c(ZmWz5q6e&e!o9-l36MiV<Pc6vz<O}<&T)3BREJ4ZMuL8JT"
    "T|=_rIa2Qle(|iJ(l-vs;+qr2PMy&-3bmkSfP`jUsH<x&#!x@yW2zs<hNtoGnw}Unm3u?@J|BEKETzEbtVHk8oYI"
    "^=Dz`D3N5Q+PcWAHG<|S-FypyNCrYNi0YPDE%GT<0A}@*IE+G2-3YM1B4lK!|AMHU*v)Z}kI~34UU2eKB)petBkx"
    "^_f;8&_s3Zadtmk@9s&2n}0Ah-GXH3&=v09K+gb)-6?j@f*4&CWGCJ8l7?^B-W@!>lC~Iuz^H;}IJIi~tA|h{oWC"
    "gUV2Pm31xLJZt{@d6``16IaqE^Es1ZCGy3Y!P_}V_K0!_ZT5q?qNVx(#O}dy&5k#ivMEgwj;-<@1nF7*tQs7Svz{"
    "VIY{9VZU^b~Mj?U6MaE^N!7uJjbD^3tZ3S;gR84ce)S}rbo-zs6#O(Mh={(5qF@G^twJQO#<ZkKs-XVZjUdNXPk7"
    "G{aEG~g3TYs6;n!*g7r42XmR(Y!$D-#roLFEXrwB1B@)E*`K1KjgnVTagmRS1$`4YB(BUy#@(~*M~7)n2n4zAHfo"
    "s#zjj6tq$2KXmO*gqniS+;G+A$MUc-%A9Q<vnCtqRxLq|$z51#6ZZus2plxVzpk+q?l*5(E-LdRuV}|A!SVUal0W"
    "0!T`aW})ghwKL?n+%U>?^QYSRwLQFw}G(B08nKJk%581#4)@turr*1@U(;XG9%FYM~vW3X(<eg|0bzJL<W<)=~|S"
    "1YBm}i7$5SK%xakLj0U%Gb*~8rO`jqIoUoum^7sWffF!6^Utut=?<s8Yb;x?ngB+N8CK~<!E@}WHzY3Uh!*vDH5^"
    "Z8rH^A>4&8;NL4<WGlb$Kw@4^_{%T33`@Qwcot-T~EWT+?D+r+CLTp=6Ka}wRVGVp}cO|qaQ7(?woY<r)`8Gt!#q"
    "^tB$@o=6Oyd!lix}IcMV|8BS@4*VhtITGPn^aNVyf-RzmI9LusuqY0qXju8p%~8HIC>gK&vYInvkpfR6pE{IjpY;"
    "!&f-Uwn)avylSfGD3q@I0>B8<H<||s%t1ehHXN}UDAOJ6d^53seYk&{{aX9;sMkM<4EPP-^3k((Zgkzi#$cg>Kqu"
    "t}})5Bxi=MM*Tf<bEDB*(U;=oGX)P@B+3q+X(qF^BF)>M)$7Xc<)8>?TW<;zpbfZ8t=@c6+F;oc^?T!WuJ(s9;LW"
    ")uvL4{xvByQ+f`Sl50?AuhE=Wg1B{&+3j5}mF%R>IY_JldoJ3tQQVlQQAM{|_O5SRfG8CvAr_syQ~LMNBX~Ul7Ik"
    "Wkt)u>5&9ha0iLDj1)^vd%0{Rv6g_+zSQ3o3X25T;MtP?gLYdZTP3Z7+sF?^8FDe|Fpp19_0;KtDt)wjOZ3f?}#3"
    "!sbRpVs$bk`-Yp<w&iZ`&Lg;w!BGFBI<sRoGH~O;IOUgfSbA-(DC%9*VwC(Gf{D*H-|N6zo3#E{jhg@aymevnoTc"
    "gl~xk2vD-{RfYH8!8;ovTUZ~T*rw)=ENXPFRIw9p*pHwa{V+(m@;fcVY0~X<^>7B#23O!64%xk^EdEGM}-Xp6giM"
    "!@y?@0GdGW7?$DddfIgK`4N$VwjeER_&dvH&C9_Ri_vFS`SnUC#yutvPlmb@IA~5vAkZD%OC@;n<)0Nd9crsq7=G"
    "_>yO?iHx<zvMfbxSkhDq$=kr8&<<<NN-?1cgH%VS0GTv_3#zVQ5EokysHGFMU#RwqO9SrFDam^gebe;{8vj3m>Hi"
    "5#|JMmjI!?m1Ji$j}-?}C>P1$NYjNSkkIT~#64}|B$!v{giVKneZpC$ngt>Ms|3un%drBU#J(VuTN&m>X=6AE<Nl"
    ">dyHs(f4<pX|(%67tC0#`ALxx}1C(Wf*i18^I1rkXl1BMI!mD!)i}_c364Lxuu`Z7~93XR4F7;5mmx+ih8#Tr|q="
    "(XF7;Z_J7#i+yYBHn6qO#HOR~zU8Xm=_*fvo*qq=5PN(MGGl2GWyiU7`?#bj@eHRzDWWlI8_P=~zq0s-^g{My><|"
    "O|I#GH0MTn-5EVW;*iPhC06rb_84*sl)`{-_kciwT0FFfwvUGPI3p8|L!}W?KmjDAF(k#A-*xD#5Tk=EIC_)$@yd"
    "F$bH{RE=@2W?_;}ua*#gG`&of?5fnEDcJX-eW;y_el&0zp$q?x+_5PTd-;L@u_!%EaCj(nXO^WH<Nk1W4+Fu6;j-"
    "oiA4_qv85pEJ^sG+-m=&8_O^&A(s9I~_W_bwDpBn$FQvE>QKY5o=CKN=gu6`QytN<7mTp>l_KlQ|RC|^L(04d{eC"
    ")E|hfPT@@!zUG#>a>1;L2}3J`mV$>bsU5)5lix0$>*7xTu7J(lPseisUx0CZcjDNwp7lg|6=kA%AU@D&Zv^EPUXU"
    "CtKm1DM=4_6q?Va*d{;=Nn0z8(hVNrj37%UKgm6)5nX)fFv@aCVAtS-fs$sG;ZruoKlZeNMvscMmz0k<V7a7p7#4"
    "ApBwjm@!A5*X@PO4U+co~F)ph04+8lDt0wthq%CB*##e<+b~GmgGhe|){!jUf)~1TJsk<*(J{Z@%t!t>>Rx4?Pq2"
    "i3sM@g-1&A)+^fl^>3Z8L(^TaEg=;Hc;49BS8i)^=PUKoYgqB6#a+U9S=8=4yP69|0d%F>ovB@ohp{TGHthROW99"
    "~Q=@m5pHBR!M)PJ9TO>?>fmpAeM)G)qMf_gXjqV@Dw`jOgxUKdav5CjOc@3-$|fIPaPN1nUa(LpHql~eF0mgya2`"
    "Cd&?Llz8ZuK9<x8MV?Vfr1c+!iQzHRC<M*>+<%|DM)&BfWjA2h~r(%DTFMNZHqpcs)|XwS1}j0O^wS$hCs%)%Y0s"
    "{O`ZQv`%*p4&NzTyRUa~j3DxVxZ4upq<suz}7$6}VnKY;dI?Bdy_CnYdF;tQqpqGpwmCe=6;FecE3Um_Z=2OB0nR"
    "fq`%?p2vU1yUq3716or-qs~Eh0NGm!B!}`;%<$1KQAWJ;6_)aM_$e(YS<6=)-?U!u%$Vz5#91`t)x|El5+EzReq3"
    "KwoApER&T;TOC-70d@@SRG0<nvGcR4<thhZXpW|itEu9oDa<ST{0whJ+jo}2aR?9<P`L=*`Yu8tNuZX|p@U8|y%Z"
    "R=4q<6u>NCzmOu*;8W6(JO6Fm3S82iNW929yAc{Atdcjirc@XP}0;HcM*4Ip=kK7l(gK^l+#GcVa1DPK;_9R!Qy`"
    "t*44NK6gLCIb>tqJI-E{?N`-zz1|YEXvr0?pg0r8`>b##df9p0Si!-=IgUqMbXF2YeTZ}hv3hz;Rck7{V+16t41>"
    "W<vju-!F~L>0<mq3@Ixc{B&Lx-JVc>biQ;l5YH^k=a*E!s0J+g<Ay1wDP~G9QIBgT;!tulC0~$L>`ocdslc1R0b;"
    "emXBZ18^m(W7o>j{FPNsD@{^w5gIB4fn@2w<SXcrrLa5DpX@pm-Swvbo42EBe~XrpL#^Wjdu(Z}1@;BoGVz3XW6f"
    "v0vs_%egM@2^6P?_=eh%f_FG01>~2QN$6@E(vq{OO{JYO)08prFi`ZGqEQNBb306C-B4PXXhi+f3<Phb>Al3*OSL"
    "UKGo_8>zeA0e<>;<wRLLGx#!-jISe_h&QcxhpnWg>?=sq3&coz*0#8v*OMD#3J`SPKq+*|QABhzc%HmHZcSgSgG6"
    "&p(MV39qOIn)7eYA(cX7`s))>;quG<_jw|2h+M>RQKI(Lu=j7HcD;l#?BVg1dR2uo_)vYt!JUBuswaE0&vxKwwjj"
    "z?V}H1Xj^}tE(vcDcQ#5#?mlmzp)b@SHyvZzPoy<!C03OrX!WCA-d{?oVsL$otj8ciW^KfDKHCZ!m7f@I2WxRMKa"
    "Dw~Iwl0Qn7Z_k72ImEg3Y&W{;H-9ySdgIGN!d&ssNd`c-^Z|*wmV?Ke(#W;3`a=1`>7vD5@pG0&iILFzxD>N@LZ>"
    "0m#e9M*aGirtLrxOpV{?;ENb|2X%a3D)zPnWh9xFou*e&iGnUV!g=GzG~`Jq{Iv@535X?6qOD|eb5s65kix$LqN0"
    "*_9}QhmxDzZY<O4?#RD_KVVM;i<RT~4%Ws`JP2K#8TTx-CoKn@Ah8)XwT*2Md`B7uSWZWJ42$wn1M%^xG2>Tt)`F"
    "FrVE0h8s%{{}yxpLL-@!-Eu%83UffGlxLvU90XMUpGamyP>M*90xwE2MrMy)!546uE}0sRT(?aDBF<aTT6%mU7%8"
    "i)zK1Y^fl81F4YILiL6TOu-*FFv~$vus9e@vXVgq0b{RxlcbinJ4O=PQ#1#`=<_IUM8Rf0MANe$@a$K)3?UC82ht"
    "mQpCMT3fvbuLRJlsRdYTDcPrd4508<a0xT65ho3uu2bNiQ-26QI0?K4l^|3?FKfE}w3uqkq3$Zf>Su{rm0P3p5%2"
    "Mg0Lke*FH3|C#}L>FYC$-FbTf{Le*9fbZ_r3?Y0O)cuA&qFawxr<!C$oiIb2W6JlxQKR_FzsJR7lFrp1Z{Pm0rf1"
    "#m14v4jKSvCMHNXlSzydt3JCD2JLWH&JUI%&Zv6ju+0cg442De(7i2uYwy<o=VNhm8B*-GAY9}o|U+lK1)4aiUyU"
    "I*c7tdQf=aXMSj@Jx|}Za+zY0VPSi>V4u<1IS`Z7mK+_F}e#enqImq+nHyn;xd3dm0ezPj(Vld>O-rWzmJ<H3f2a"
    "ZiD8Xas2mVyFv%DCas1Wzys_JG%02&T?h-{iBV022?3*4o=r6#+>4iSR)0Le@lL4W$BqoL35eJ%Q!9c3uaoS<w6O"
    "H>TsnUSC$SGg}lr+6<%ai(LbFuMV2M*SH-MQY_LI^m;YAAHOxjp6wnwsQ7^EfU{xfo*ijgPwsJ1ce|aWe;1hc2z$"
    "yA_b0RWCFk_^f^x(i;eK!2;dE(xl=P97`n13&^^gEXPVufp7ygW&d2}C2z<F^Nht@9SInxV^guHYE5sp15j!>7P?"
    "_rAjsGgB~yb{0Yd;VXTv1Ud_e7PLop`BOKwu=>Ql$_YSJ<SMCI3L{AF+VSA;OzJ4QsT3jU5MfKrKu71ShX>kaOgN"
    "jhbS4+?xB-{5iztBxlvp^EVJ3jj1!ivs999M4pRx>K~9r4+$1(A*RRS&Ww`rvDJQr{a?1sJO7O7g04^UQF^4^{yI"
    "|tR`J60~&t;rVz4^A(V|>$bd2hpWrACF3^dC0t2EMh?|CY?<|nsPzdW&hF8h#zjArQRAQLL*&FMTD$&%SgVpZ;_4"
    "aJpcGJ4UF0%z#SxXCdjEyDkW2PtDWPT-#8n)q*&&c)iU@yg@OC@n6a!>Wu4H}rBL6@Q(qM45SQdDxCmxvI8Zo3&%"
    "0)n1v7rp9Q?xTc(F(Bu8^{g}>LYS~3j;%JNVu+<+oVBu|LJcG^c)|;x+63zHx)m1ra4<Yqa0`+AyX?-8y82Pa3GM"
    "Hz$KY-dpI7gW;50e=A^3!28w)+)2`s^9!XimMR<FBZMxv_0@ZB1E^@xI4=8E<T+;_`o**;hI4s!bn7ZO@EKG+K5u"
    "t=1i3R7nTW!f&?b%@fPEMg_ZH+IO(hJ}nF0Z1v+h*u_NvDh$s^3sdxAtKX*&ok(#A;Vl`A9D~?HHoHKHZBE#2TzN"
    "Bv|m7^Bdj{(QCP(;s|5u0k|lIxaZvZbi)-*g9T3sp33b7A9|Dd6;(20urQa(C4Pn8HLQYO7MFyZhoL~YENhW(J-s"
    "QvP+eaT@b8bM>8)x?e`enYMu1R@{I*A5{^+uESS!=*8jKx8lSm{J-pWYT$-SJ2<{R<cqqz#n}n5+?RKzknBzL>P+"
    "U>ZiNcu)*<xxB#GE{H#tOLt{`*mA3I<<D5`H*OihylyD*XqJp7x%JIgJ4ZWsp>^=_igLT9+9emo???p>d<|y6u2Z"
    "A8zAo=EQmCG+V0~V6#I`Nb`#kyT+h^TY5!EL&K8aqsL2zReRXv)+5C%*ks8~QQ-#mffPU?;m8)evwNHes5LPa;C$"
    "Ew$`f)vF%K;8nQ!y*|G&-_5T=zqvW;<+;`+=-+p<1qrGvGujLQ#%>)QtH=sl0g)he<x5y6InnAc%$|q8#bXspmOw"
    "XB*?dE>p<U7i=T&~yX#=|DFFCBh#NkApU(@-w;6u8uT<TG02>@esBRut;KKX;eEMEV93AU>arEK7Yfm9@$)IVnU1"
    "0-gH&K&NTg5&dOK=V9T&0s+JHew*EsU(=3zVHn@Wu%FV7oSp3i&~?sd~}LiYn9F$fYXImrCbX<-p(PK5cP&95+=>"
    "j5CgBI6i_teZ5kZvFMsY2+B}S)0ui5Eu~x`$aZR3KE~mP`|c`iSLi0b`G$NxXYC3xa+v@a_6<l09Ci)-suCo&2nL"
    "=pl^T9rV-$z!?{h3mo!R^mkA0wrLghS^yioHFGRq+^S08`XJjrZSKg+*sp0+rwe#5%98r7UJrHqi!Kc%8ryHu*8c"
    "6sD6Ss*2^f$d=~lAEcmY>Hk`Hj426Ps0vqF%yBM4Ksx0R0p>*90h}M+Zv+i=Xxmpni^}!Uub6mMi!0gNj_ET))Sy"
    "eOqQgafjNW<b9BGz-;0_Sr-c&I7np8qRj4Y%jL2gRafsI8iIu#Fw*=0ATRB$=D3B3>d6~AHdnouK233nRITH^Q+m"
    "d{Wn4}zY3ji^bi*)p08MiUduP}lyRIgeqt?$$4>Y4e_pTt1*ijEcQ`FUU_o+Rc|)Lu;Mk!W`QNu+9o7%&-+7S#1a"
    "GWy^YEK@{6pwwXv`5}omL5-7w_8HP~F_$9+-tOPL8|QPbw@gtVF;yE*ig)}Ix-{G@zR{QioLJ4-)E&R>S@b33N>f"
    "6#?4%Sxmh5;F-hzm$t3;}&U3}{;WU?B|ft0}_S3m*cdQtWvBd$Z~((2b?vU9w<eX1l{{IUD@oqhTH*W<&3{omqfv"
    "v{uijzXupdpX8tOxuVieZdjhYL>F}#*Svk3w=Oa&N^x|-O8=Y$+En*!_eR(<=u4Dkp}>8vFLPN=0fA}EGqB;+h}4"
    "L8Zfq%D7L=%p3djw-)z#cFSSl2;q-Ki)Z7G<nxqfmSe_<ge;jQ!CQs8#aYoi&pBpkq*sj)<?l_>v4|yQVFPBe1;q"
    "5P2bd@KJtKOmAOs+MRzC$ZXo2qx}>sN%ng7`F+d7M2Gd`ciZvpy8;)C&jIfTr56gFtu*Z9+u!6m8MuFvp@PLD;Pg"
    "1IJIMK4F~WjesWxrVsXcf)=0AqQlUU@x~v~0J+iSIj(z%=NX^d-+Q&EdR8rR>n=%SnfMiHFfw}v?+1V%v-f$iED;"
    "To#~NuvY1c}LQZ#sCnLphkgk(swV!7P<fw6?A551$uL=<bR6`cm=>{~vwhV}tg4yn~xcIHshSnMVtkP;tD_|prtH"
    "=jj*ksSTFwP)!$`-1zZHqO$6W{$}}sb`!$ls18z0|vr$f&0Pi*hijWM{?$M9gN;#oiVm+P))ID@Gvs!KbS^!d<qy"
    "wamwx`B$4xmC{<gsh0;YeQ^-`@ld>qr{c5;`%#${;4w|YoxME7UKv(r*jZ3QD^&}J~)wz;};24e0hi2fR{0z0qAs"
    "38IrAfb04YsH6aDRXIW%B*@&d*`uL9nvzQ@6lOtCADeS58j1p^|ECW%5By$#$>k;6<?Zkj**m8YXMF8r%36o1BWq"
    "-BhK$;0vaR34$-ze&6_nXtRbJ)4PA5moNCBVFXE~*ox=NtcA#RBP{A$X+0^mtFU7B?MVcLU>_Q|aq<8G4U)+rU}2"
    "$)WC;olg-K{^8)ke;@DLqd*YxrHU`XfoK{w5AEd^AB53>%HjC~7=hVn2p#`;Z`mP>@$KvIXgCyaR0qbL8lREMLDZ"
    "`|5<WX!paN(~U^(<?M~NhMY=TB3J>YKK9}Zt?Dgn*VXJT!`TUq3IWeQg9Jmp#M>&5-J{}Pl8div#nO@@JA!}Lq*F"
    "DO2d|L321}4n$&;cX@&we%m3L`vB(*6&AN_9SBjoIrN_)WQWO&G>}rnkY5!sgco+zyiupk3{(#K?3z(y>TV5DajX"
    "_n3{v45;Bv`xM1$Ctp-3EDgl&PC+ab1iN{SKey=y$s8STeDgJUu)_3lWsk9x>fmGgC=Cac9j;l~<8d(MmqGL+vS^"
    "%vZ2|Pm0w&zfP^yThj+$fCkas9lO%aQ;N9yaNjim>`1`BXqlASeY*Md>)z(`-qyDc;-WVL4tZ4b33T36@Jy<Fdf<"
    "IG4m%}g=|w)#Ni82JK!g6izYiZSxaIezmj%BejF=Ov9n_cic6XG*a9<z&q9l+@hYDcM?bX4aJpm(rg?O6hMi1%D0"
    "|Ls;=t595fnZWLU05{~xd_K1OGnpSY8ag^#($%ejr%KFM{Dhgj!;|~+6umT>PCTBm@89Nsfs{0*A#IduMVUi=i~@"
    "Ia$dDf3+u$1-mgrT^Qop&%Sx)dxJpqFjnsa><Cgvqri;kQgTpOUzulW@)++e?5UMrnj;LnML`9Db?1cO`A2=D0;!"
    "ZZtVrwhFm94XTI|7AI#<T7kYZ~M(d5KCv9sS%pjDMyMl?-R_5%hgN8!_MOZ_;YyEJ)f53D>&!ff~dC8<G7T2*stY"
    "ozW-37z)kzzIyt6^C@P2P$)EY;<Xi?3;B9eDo>)JqVC-&vHGu4@94Aqw<*v9o*LJHOYbS!08O6~3V{;RWhB`xME^"
    "+w0!)%<eoFF8TLF*_3ezjL0(fGeSLcnu+<F8^Dt;whDweD9K#n9PLIIy7cjhM%1TA1hFhRgidHeP0POLBf*CQH!G"
    "_;_J?lEyG?z(hrTXenc)~Xo=qSMLW_HzgfX6qM3Y;%}41)J*V-Eo>@MFVw&Ejg;VyoQy%%w2>hWAyZG#M%gB*+ms"
    "$V!lD@qoahZg&9L*vI>O=Ketm<K_U|gAmFH+OCmYr@E`5fNbl5T*i`zdCr_eppBrfBkm>f(_q#vt9q14EMU<A5mv"
    "B*a1_v8s%P+s@*~Z0Bt;>XOforBF3D7IF3e#RKvE0-LR?zEm6S2`Bj}KoTMc@AxiC!NrSW9_~pS%m)Y|BnC=?<gz"
    "2KZ5tPLxcSbs&lwY>hDW2V$q%JBT_PJBJ59>>a<_eYp{DyxiU2`$a9y%Z+Zp41Wr*QWi(FyRX{XjCK!RcH>QTa8@"
    "2}@#XEKqvOM0@WUsnp}m72)nBg<em*$-^<d2o1Rh?Qi5jj<eF3G|7HdtiMxvzrv2upkkD(gfa0}~W+8bb1j|^%Kw"
    "hT^Bfa&W3%i-Sg;ZFukLbswjj!$vTup~DmiMUixM<A^emgK6~tHO~&p-48EDkK|E#tc!9T+-PvSdjhUo5acjK+1M"
    "*hGO??=wHbW9nKy}Bu=~qnbLX0wb#?TK-Kk*x*RvVr;u?orBz@;kb^17H;_BQ@^GsZa6NnZIA$)#B@2RlHXMUP<F"
    "t9g@$UA^-xM1-etmF241p^~Z**(gI6Qv2dkoBzLEd8}r;?BF>1IRS^D}#cjc8we{+Yt^*k;Cvm&F=^ov=^SNuq?E"
    "yo{AtqPFF@X5itoq}?P%FLzIN)}JZ0HFAJ>&(=5!>*s@8yQ@7OiRYA!!~@X_(`=#!^7C%Av4D!=O4l9y$A&po<vR"
    "^y^w=#HxnGZkG{_j#Q7p){A+2wqznaKkxbgDvV0WYLB+x?9Wj=-aTNb;tIw)R{j#Ic2vss)NYZA-`zGI7GvN#^_5"
    "f%jmho*MB!V$wV9XTthB1+D9_Er=D=1q{cY889m>^6Q9oTc#M8@=6?ijI>9P%)jdivs(_1Pj%?003O@0fJ>JpGQ("
    "|UiV_DRGc};`&gj@wgq>H#SH3D^rd@~B@eo(hojqC*?;}yy@5HFDhX-;^9&SJ(_WyviBKx+F1^)i`d)cpMgMi<?F"
    "XV?xrc#JQFGnJRzpKr4myT9D7_dEK(s}XtU`jVTYW~}TtTTPa?VjzAhvz6u1CdYSZr1zPkJ@aGKW}ESa|akF={rO"
    "KjjzT#Iqf->&X{IatFW&PUXCR!KA6WqVK}kz@SRC>kvcmQNZ!YF&cs7?!+=nZ#n)wQTmb;En;F8=z}f}e_+irts2"
    "H)JW!%vSpb4{>gLf|DYuo8@31gNG5w;TzQFAoi>3tYpru_(x&s6-y)-Nu^#c;oD{DIOP0s7)&#GR7WYkv@FQ74Jb"
    "571itsq^F^97=51Bx6Mgsv$R1!mEuPMKW#DU&c9xP`-VrkOQ~0gu(4HXd^@ftymuMNvR6F7AnHNhw>QVBi5-v}%$"
    "%0C^IL69^7GE}N%5@47CS-t#s?2NE-2x)7L+q`1i!jEixT{tgNX$ji)MHL^+6BL^Qg)AbgECN7bA=ijx@_@8uVhC"
    "84SqY}9$;?Yui@FSEo$<oTgCjHQdmhLWpwOdC<a;7K$To#M0OnkgHyy?6_O2$&`trbF1tW{|OckOra7-LFmHnUGu"
    "lJQT>Z?lT7V5vDmfb{HE^;uuXkpyFhyE^(QT9V{eee$kh!O*1nWjy`x4|tS4EX22u_Lrl(jnbGBqd=yDI_M604t0"
    "60HyaiU#mrT^psGZ4FlThPir@B$NB}yqAd=lbz%n2oNSS}~B-+~CyzleR|A1eE&8J>5SJmJ)<d<PxRgLiu)GREPb"
    "{aRWpU|!AEA<~ZB*x9>JI;zF9$BU#*h%+pR>h^^ZB)MCHqCM3wano*X4#yev0zssMiSL+iE`w3?0EZ!)0$2hLC}}"
    "T)Kpmlo8N(7LGskwSUsxw2#M<aHI_%6`y#)FJ2Zk7oOrM7Y#;0>HKJxRj&&r8)=Y@cI31LG_Z|*~_jAWKqzv>;3("
    "%Z3TmM|JWFrJgAKDH#3Q9$n+gTiCQwZ8g(sGpNHVV7mu3?c%4Ye12pkT>}(#RRO8gv1rfgpx;Bnjq3&v47w$9!2r"
    "XQ!)%kYwO-*)dM-4`~<D_Ni5q#t(eFBB9YhK>lzBQmHywG2dK@fI}#*dSfmM#qfbBnJFvUu@a?(BkKpig-JD#LUz"
    "(?M6>3q^}0SVSo!i%7OGqyxU_2&NODb}Q;8HW^l3QNEuAWL&g9U#f*L2WuY&$*c)Bb4o9lyClmj17!l0J5E!9^_#"
    "`>~qb<VUXDGY)sfZZ~zYJy)zN5Tcj0u*ebuiCCZI${Du^>*)N3I0~hREaUirN|}9JNKayL=bVNxiTec!gr;D@fhT"
    "7;Fy-!buR`lQjb`BuCOX|COQ%xZpI0`$dW!^r;I%M9;DzP77${<kZ{`fDjDkIlpOdJ)Q!11GzB;~Hx83e@s<wWSw"
    "1OTuPzqLhO0e<RyHMlqt0t6F1EE5Tg80m%L)ARlNv1iyVb?2eNbAj1R5#T3`gglhx2@cTz6!AkB$0!PDM?jeyQpb"
    "KlXMyo1`Pm>l+Z6Lb-M5d=GXR#GXat0#)ltaixAxmIpYEqpvo5;O)bwRXZ>$2=BO9=92{$$}MJqel?=n!+?W=9q*"
    "irEA>2%&h5bC^Db8zd^@EgV*p8NW);+2JzbSygU=EwwG-;eqKMv2i`%!;^g>M(PTTjYU*nSVGj)wa-J(+F(1lKZ2"
    "ylVway*pCnNsDDF%Q-08dMd<itzxd5|vQmNlkMcL1yVZ))yvsJpu=%_^gp4q)wS-)e_E;)MkE${Z*nDza|MYaKtS"
    "XPng_kLV(qKJB2b3OaWM12v(M3UU#k$uru0v$`53}XY)~xNdPovBmgRj`gV%vy-Y!h_#{P1fCchm59Ls`!ywrWgJ"
    "9J>A1WbxyqsgP#}o=7rVF({;i$QTO&KZSB|3Kl(a$5-Q~h?j)sMER&{YpXC}JgWC>ahLJ;(Vk&ygi{Zt^QO4{km0"
    "!a7i0Dmb!m=Z=cW@@C3tYif3;W7YdHX7E~@16DwdaFov|2-r0Gb(Bu9HaNBhs?Wtlo!Bh<Qekeu8qF`3Tvzj{>id"
    ")<>Pc#%9`_kd{hX4KaI*HsP-g{mxTr=ZuJ@&4U_Hd<154875~{6&@$vh^)1M;sl$ynJs?>0<PR4YEqUqZy)&EK%V"
    "~q=taSVds=fL!Epa^1&P4cVjMRZOE<nsuMN=@0up;}WbhI!rK=_)7r3_zW@k~ZSjSo0+X)rrNxsiOG{vmLCREJe@"
    "N+Hs)?o?AeuD{<j_vb=r#C&|@xF{<9q_6b63!MyLi+<kR)c)ELV8XfN*?Qj1EiF$yIAd7jj{c0ChOj?N+w@~5*(t"
    "mRRh*L`|bhLq+;plkp)%Njk(a*cTQBik7>WXL@peg8S8DW+Nd_idsC#QUyHxv*gTmRHy0X#%;xLhxBLQ4#7QGn{X"
    "y&(KO)kf@J6M9jT!|6@fbz$`sFTN<8K}4N&a+}_j>eL8KAoSsQ_lMUfdj~&8+Xren0Kt9xbnpB9-RNj<|L}AWLHT"
    "QpWYKe2j7G~@j*LPPSUG`Yr4*Wax%a~lN-<NbA<uHx-2Td{%PL5r^&Ek`1;(7buVr+8Or(#qL?zL{!(c7JuRk5C?"
    "pnM9n(6q=g}Z`*AL_9#;KAeT4kJO{r#3Q_UQ|uy#6F<f9nuw+rX^r1{5+=9<O?tXE|7yL4i7<-@Ek7QB)bIXu(~&"
    "Xcp+P=hxAn|)TU3A*^S8V@-VN!r^*7)$NFh7FW~{*0)XfUmgyK}L?_g0+YzPI((+2n>4RGdLzr;MbnU|k@(iu8IP"
    "_IB-P*`T#IBQc;ar4D@apV$pQYC^W^0nUw?tOQ$U!W;ZQZOe2TCk9v1keOpSDlOg+_9Ej8SRTd0I1_SelHjvB%Dk"
    "<H|_mzyQ7U8gxj~USmh3<|xC+jV|cuF6i2!>t-Y~%~n-=rJs@HM(PIP0Z<*15AxYR%<n_G>9(BCScy?7%*EtAV%7"
    "nI-tReOG+SgBYJ>N3WXi2Su|>%K_#)b%YH!hF(qw4LHUe!yObo3Nkp{_W#FSF?as~l}JS4X-t~z5;j5S~K<`5FR7"
    "&ebDLAq~j2lNP;SkIb^m8T6MInSHR-Wxu#ReEG@d2d#U(t5Xg(|fzJEeSJ1YmXYW!Yn~OY=J-uI2$&uVJC3|KZzR"
    "|ir@;=amy1{+puYHk|`<fGDDjl3!W^;gPB6<Yw!TP(iawq8w(UT5Kki#PrK@1&Xln0O8}?{v1~^o0F=H}gg>>iQ9"
    "-9N%2A|GD#NVMdUC!{Qg`_T{+ozK4KjhxL3toCdq35#QoFGyTOOGL3mh0$4Kg)qCQuh=N*GXC1UV*_p#?swc-~|Q"
    "dYwAMmLTmeZi}83i>rm^(H#imR#MtU!3DHIUhd^&nAWwK;lhaUeynBUR5xVYd`NbJVX^BLL=59&wXU_{)i6ZX)M;"
    "~I)K%W7ZsE{T5=*#{YPs9cmZ>TiIsaE*T&|&}h#po`*_7J`SC@yyW@cm6H?7I2e>5;lAKTGxd&n?4#`=5HMRqk;d"
    "j|s~f%39IHaefzyw>I0M_f`GbBFPTZcPC#Jj|=NzKBjh_tXM}Fd064A<CZ9#YX8A>X@l*J_k9o+7Kylh_egqf()$"
    "MmeEuEJx6=YB|vEksCuX&EbdK;C$K$W6(Y=~tm~kLAbq~QF2X~zN#%)85KjVf7V(l$Q<R2ro!L?eS*HxAmc&)m=0"
    "LIuHe{H+=%pn<{w(n1Kq;auZZdJLZV>i*KZKdUa?;QfYK<t{4H8eyMwRyZ_N+mvU`L(^zN+X|zwJ*mv`~>PR<;sY"
    "n?DQ#8#S=Yn&`hqnDqo(Jn<bFR&NWIap|m(gU7PhH7B-h8=6HjE;$O1OoJ#ti1dJBKvVHgSI!IR5rhrbs7nNrCzT"
    "+KR=f(aBLvap?nR^y;cR{jvndAdbX8Yv34)Hc2p|aNxU(?=5jsr1Et-H;Q~Bwnf4AM&V1D!@eiZIxU2+ydig|v8L"
    "J#lyjdH~t5QNjZEU9@OM(QNLD&}`XqfrngLR!w{ByUKtWfVzDA*_S>l>KPqOn!3N$2MtoN||!a!*nU<Efzm)rS>z"
    "QvUb-##aX*uk?V!ASf;?tF1HTz(GN9stiA!<U+u-rwd3Vw)sROHm0+K=)s78w=|%BAt1-`^sc%|@nknY9>lDHOSw"
    "W!V(Kp>i7k9YDFLBe0K2!mZ6~L=CD9SUraMZT7erzf!wWVY$v|q!S7jDPsb)W+J?dkJCIy?dkP*{+NzFSVglQ#Wx"
    "=<96`DRV&S-oOb}RS+9WhaSR#qfOC@;om{t4R<;PE(~F5FSNzHN$W7jpkqB`%P)vKWhB0r6poIDwv^;FHR2FL>1G"
    "@YWiC&PUNM7w*rpM#e?Hi>veD4;>yiXpo-KNwJ%r4C@xXu>CytE(%T_iW*Y~%=$9X9e`bh9Smw|h50rl`xwNPOEY"
    "4NHBzxknA^`!Ln722L}pc=H%=tB0XL0cU!Y@iyn*ZW)>+@OUHcpru?<I{*YxNmA*$CMbDWXpJ1-$Bo27@YWum9Sx"
    "+19rj2X{}lUZCC}%6liZp^~q|^xG99-nB{at2yp2c#9|@S!1MJ^yqVqs8zak}di7A6Z2b>AZmNfiXnaA#uw|KdPZ"
    "7cpY8f+QN2$1hGZ<;YtPA|f(G`ZH8N-~S(X2;;u42DeQ#3DP2-QV40VBXX!-yep{Ldh8VX2n<BEMP^D5m0i)<jc4"
    "2BdIMG}hX&H{fHQE$1^pXy{ZzJiy!iDD`7)U_?|m42+^mo|!25rbNFbg&}uIG9o?3j?Cdu7eL9O%!li2@;)m?OOb"
    "#Y3RtkBUi>liaRJWX;;D}diSA8m{N(4?CAicmY-?8JSh$5j$z*vD#8VMMxya@()M>(@B-GwDxLOOU#hymzzp7>YQ"
    "H}YWVs=LhD_R8R?-qk<7UEHVxF?m+EZTrjNIOU}36Hf2O+x!L4~bAt78v_;TtKMI36f#W>rM!fG-6$=c@0-co`)H"
    "H$#E4hz%M9x0gPn!LO3e~G<uUxq2{w<Zw0u_)jwcX?>Z3~eQ1s-MrUigMKx@X0T$kXk(@*F;nno~$vKo=pdS#2bP"
    "mlS%67_SsS1XVk8UB#B$g^rruQXANEFlw4nbD)sycSGzkP79dz@_VoE{!0doM9~?<R$@_D02WULpqBuZPD!`wz)S"
    "t;dW%2M!pFRe_z@Q42J1RwQP=GT?<p&TcP3h{gY4OlUyUR0xY0j}pEZ_mC?SI6OkTUbYEl@RAM$#o(^6vS1DCJ2!"
    "Ax1gt$i=Wes}1?-QJq)Mx1c3vNYinsq85k10xIGa4`C?<t~j2UFT-y&BLr^K?<v6r}b_$7(|C}Ff}l;;wXM9?vmA"
    "O*PN>S)!z9LlW+>Haze!JbL+BFm;GRvPrMT<zU1!BM3%jP~38yINy40F73M2&%inykU~*FijUS@_^d~%Cunj`v4I"
    "QCOohOd6TIWYZUMCIl|bXCt(d7Xf-}94TN6#ZV8$gze?RuEauXDT|K~ByTgBg5|s|n4L6QPXew(#P+~MrCX|dqZ1"
    "}SP%C2XYJ=tTSGpOi?39In2MnQso=qN@=xUv=)0I{K(efg#u;t$_*hJ=l}K#C}4&>aIdt%0ZDGAEz%d@{rs%p}EP"
    "*^dw&G(KQ+>poEnWr=x45*dL+Ia7ls76HPV<(V!J!dCqv{VSUnKs;LNVD_f%mdgpUTDqS?hQ&>RjtO9vrhW>~xKZ"
    "q-18+9ZBx>80*lZqU$>*k_q50DmzahYL2r4`>V0{XV-P{F^tzioLzyzLq89tbP4##5u@M!mVTd`zYh@U_b{TzDYv"
    "-a3U;h~2-&K|pXoCxEbDMerHFGPDs^bpfw-LKYQUC5gfy~Esce|F5PP8o;%PsKjVe4$HB^&mPq%4SN}87tuctyI}"
    "mZHSS&tb{9??}s9G-C&s#2eIpOp>BEb0{rgYbfL&>A40v+UKvM8HvQ)^gK`@hLtY6FwY5$D>&uW-(Z6nC;PufQB="
    "KD4+1!capvt|@rFTpFr$m7;ScEAMfq5aC9u;@VXIODfKVV8m*dV#609rd4PmL0SwIRQ&gPbg;&@jbt;4WTLOFqwM"
    "9lQvf3ojzn?dGPHd!g>)9ZXa;Lyl#jfXcsYSBXH-o6X^5%uZ79n1k}Ma+_>log?p3PKPHjHdEEDML4ewh~PAzwaZ"
    "9oVIaz*zaH)#NUzIi79FZzeKjq^9R4f#N_d3|Zm7R(4}h&*x4<9L(`Nx)qh(gl92vc(hd!+E+GDjaqdeXxwgNhEx"
    "$p(oI2~@`uYCN65O5GofwhI|Foaf5hiwsIL?)RZWV<{iXl2H#h|Y9KC5*KIRvx#U7Iiq$dRzOZy9z4_vbMNWgG%+"
    "hfJsyy#)9i5fiZ*-LG9;6K3ee{Z?Kim>HSxI66K(d%`4(4uy0!y0jw|%qZz299o)I-;-$kAeV=&5JPMZ~v_`-r8!"
    "kt<hA-#!(aY`A-6qO7**!HIBu)VoLTwa>UTUJ0Y$9q7(g~oThH0lsuCGH8@<-GFnkfJC=b?M3)I~c4mRv(UyE#k|"
    "Bf>(Uz7mYf1$@BY|7B(2TS7uPKHl1acK|wz37dCRETnBHy9O`HM5*!rhQrfpPu$=xs+#UalmSgbk(?Je?nyAdWU="
    "Nk`Y`yd^>)l=JI+enRVj=}#O`&_%Nnqxt0c&7PoKJwxU{)wlukR9g2n2!L3F9K*M*Csj|G_Xo8^rzDz>?4Dim84>"
    "?rutf>tHgb?ahSOeLz#pcP&B^AdvA)TFDsDB}T;b%(#(70Y~%nYZ}oR`lIa`UQUiG()2}N9{8PEbU4(>3|3)q8`j"
    "kRgTLzOV?Ne)+Dvh0`?j#?x1@p!mxD)O+SOkU}Ptal9!JIU~Fhu8MLkS8*2$of6x&FTGs;BulKBF|4fB}g)ke?AK"
    "J+ZT2i-3Rc(OfG<~1uRP8e$BKY4Wi;93SR8YD;o3s#=5u%R0l4#~>5mOW{{NbuWx>5XYtwa=PgFH)&N^Q4fZos^K"
    "Y4hLum@I}_7P~>sB%0ZdYlBY6;G#P;_+a|BkpqUn;DhPmeSN5dy>*%-ZHaZ6XBbPIdKNN-lA&ZHt0TM_0nvcU)7s"
    "!D{f5XBG+QFn4gq+U^}!louU|d3MycO_xIy&SY^jm;)V#!JMv{)X!kL|SvpQ<dw?8$|Fj!-E(pd`GA4*OlEMNHS0"
    "!i>iG|9jPfrfLo*U^^je@1zS_WWjS=u+v{E0lzec{q+L+@afClI~$~H&*#KcNBf?aab=J$C9oF)iKluxd=JAFRi3"
    "9mo*J64p#d@4HDmq@EJ{>B>9L30UD_uJYbFE2fLs<iLhAx+J#bn-#ONOey_DHn~|s-8}^<O-JpBOel&C#Rfng<B{"
    "9wd6PqaQtEWqdKt05Hj)y*DKuqq`BgG7ZF@HKeJ%W>0*Ykh``<!sTE;0hffOHMi&KawW05^yYKG^B6BoW1n!F(L5"
    "X)!m~O90VYRMV~<TY9ya`1N8j>r*`^>B#r0?=aqDin9JmP22>uIJkC#Pd=o?I9^}QCs0foN2JrJ=aW*c)Iv|q>~5"
    "TbN8auaf<4924q`dI%mI_*2gqru%^8PrQSk_DL(dmgUP1MTGqV{rx}!fM(kWw@<0sX5Zob{Y+PF$+R8({U`x}ka>"
    "V}QeCAM>@^9DWb+~m_lZIG+Q^>7RIDE&*<mH6i}MdOfYSM=i5Lh)0zx8T7|4R)I^EcEpH7ZUT1><G78GYA`<Pt|D"
    "tKdjw_w){V8u~O0kYhP05_aC)JNmDAQeLEBM0#uS5rL>t85r>*Ippqqt#lQgx2Owg`=)EU51gNG!$i;FY>gh20Di"
    "+*Q$KRliykc}M6T>zf-%vocIp$QGLkO`WAMG|-3Fx&xqRF!J9B9rLcZ#_@d979pLEqRp{^9MTt*77gH`V`c5o*<7"
    "z<=Nx!1GRtAh$WCE6%YRQ_X#-n0X5h=bHNnMpJk5a-LqHkFmCKrS+O|P_Lgjy=`HiDAnOGK^%3>tS!fY%X?)_9DN"
    "69q@T#Gn13^cKy7Be)1Q;e2>aO8G}N@b9gT&{6}#tIAHarh$hG$9P1?KM?EUHN!&gu5QDdaXyWPr^q4@%d(KcRG9"
    ">XW1@1o7Mrcg>s=?Ro>gIO5?bp7e#2Y9mRtHVfN#S8Y<<U5FW>Tgeb6D_XI_ItuFIU>|!>u)%Ro9i{&@vdeghaRb"
    "~W~8y&9b&aQXLa?-C5Rf{HB&a|zWq|j3RtzayTOuWd>DCzN6W&5t5i;`xb0O`P_s7_bXfS|TGcE_Nx0cntwEi#O3"
    "?ImmICzLFj#zUhl<bjPIVQz6ex_!cs@ZPBwSDO@4XW_ihJ8K(*u|GR=u~2M9AfNEjm@h<v;B4(%x#QLyW3AZTTU#"
    "#y?^|N(QCX<l=6TmBX!M^Vzq_*WWyk>ngCwQuev>hB^bDZf*t%<?uxFJb$AC1XV#$@bd_W5c74@eB$~0bge);ut<"
    "7vQH<}Z<zXyeI=vm^KKU57B46~n#=wG9n2v7zCl`^tGpt0Y8kbZ8%Bzt^E>~}8kC)Ljhay2;gPQ5rwkN*175(EPr"
    "+7&JCxT9fdyIljh;16yz+#P5E@@N3Ho)%OfK7`4R-9S78*5O6Rmy^A>*Ls);<ki<`2=TDH{ZnaWV&kEo;>hBhxL7"
    "W_J(DlYk6B`iYX4!Wq8A3^lUR+TDn?u`Qx~y<oW-%V~hX-o6i=j`5|xvCDOiI&N?9`&}v&d{0upZ*~0dBDBgBGUe"
    "hc_=}8WK+cer;qo!&=AJFLH>}G2<x$MUT!vymh5=M`V-~_rq3XonP+gNowL5R*oD2Bkxq&T~dXiLX;)M8Ksy)GtW"
    "-9ke7o2AiEHzjVaxS@eHG&Rq_@K@<YAa)K2c@zAd!LO4ewAl};=iAu6z@Q}<VHcVDzr`&?u4B+I;SNnXKh?x2z;u"
    "I22cr|;jq`bjew1YSri}KacxPKjoI0SADb5$cx^Uf8Y4hlK`^Q(?(LahMKusrLry2gby>Dz5%}8-O$Gc$2KHUbO$"
    "h{w;gTvEk_wRcrrzZ@?Y$!WA-TnKi4M`chuyC49;&af@!R!6~nCaHN+V!BDAKptoOFD`V?H!!%{<wSWpl0s;w7c^"
    "&cs;keUUzlyk=tF8simoP`YQn^hsV+0j|Ydxy8<sj(xQP8_)EM=I09gL?8ASab-MlQ?Dx3)(bF*(vnfnSWx>`S9P"
    "QGMW~gM-Vk>ATY#g;u4&p`&=JO$o6C2}HYu!FQ*$oIuR+rR6BI|zLwG)r&P`OID>NK-_%0U&ASvtQ`yh!o$x~_nw"
    "2z*Hh{!Yg%gbU0wq!uXplmk4P4rl^a3qZ8$!+pOq;4r-7Zh+)PTsNri*L7!}-nw-WTqQOzQzbZngaLNovD&9d@ay"
    "<OUK|wi+PAWgmRvRjcMv5$z3q0pVcD18Fa5!U-O2dYEu;bWA=xOyrh~r2&iC`;T{b<+XBo$??`Rr2&J+>t)*)yJ3"
    "2f{5ml4`-F_B3k6)~ZyTojmg%H>2V1fW@`qeN9j8J(7bnu4XK%#B9Su@x3%A2=7*@!$ys*utBwGdLcpaVvM%?Wgc"
    "i-OF0h$0Q~<1@Gv9aN;+dn@nu5E_5e2h7VW-Msx>A9ojqt^2|grfJ<9v_x^y`?Vi{JLxcGwyGloQu0(+&h6|NI9B"
    "|1G9hJrJr#?jZF(zhCPYUWlh-Kk#Cow&)XoM9aXkxR{hWHMtDas?lF}%?ec1B5d0oSk@$S{(Z^weVzPlx7C+kj2*"
    "?sOda-@&k&ZXl4+UZru7{J4ASoeZ$^ro}%MhdlUp^Jz7lM~EK2VB0V2m<2ImrCr6|LU!v=huVJAvWSN9dob(?PcM"
    "%g>u`Il4nN!cQw-!!@EW9ev+)^?vx!b#yzkb<UQ`ET<piz|Z6ksl<p@%x4jtZRq(mzJy0y94gl}VI6b9Vp&_&K++"
    "5D)fQnI|#c9KO=BolS?XY0?F^_}pGKw05CAL?<l9zS+zu@Mr?E`wGRK4Tu{MZyASZ@je2&9knbtXUUQaUZveLJQ5"
    "Bp#)}U<`n!)%(E4vHWp376s)i~WQ_V5Ld$h|+8>5)&Dr&6(Lkd$?cC6e)*rajwKgjqy?Qw~0?}A5DxuePr?bykt8"
    "}KZLr~^$Cg_<zL5fW#mmq1;j8x8uqr;O=b4Z9=E3kxNX%qg3;u6&Si>=-x)2h@<XLAjo;bQ^Aw7Kc;z;gJf=Y#rf"
    "-H?SR`d&3WyAowojPG2-AT0|D(;(D#s6P!o?=->EI+jHE7~2u+-+?`*<`B)2u(@n$52jJZR&o4$jX(qLUjBp644m"
    "7IjRgks#_q})C1I{?V}-k++HOsg-Sy}~Y_g`|nszZ(zZP8DO%Vg^@HHfc3Ny0Q0BxV}1EB*G-7v|`FnNyc9y%Yky"
    "0*%rl1NWhUoedYhBL(fe!1l;G|eAyq<ot;<%n6oe~m9x^PtT1Td7Okx&>fwa`Q(TZU-{h>ZSzODVTN^I&fUQu(JO"
    "h6%qdk9kpyIFx#h%sJZE%UcBKFi&=egK`DGXeZrF|zqEas?B%jEidr32P3(wc4MRIb+l_}h{*V*<b*4BRTAilVsT"
    "^WX6k<pXp)Y_@EyO{{z&3VmZ_-gfAyrz%yX>y?i;=dat9CRcA8b!kO<E`E@6_W5OR+7K&rc=7>goQhvMkA|EvyHg"
    "kh^7sT*bCP&=i{SMcy#o2Ie>bo_zmcHB2UL7zO?MRzTLEHqgNJ>mcH#tV!rWa%R(5j(7j6)(~o*lk*dysThKGduM"
    "0&2=DoheD~*S5#@o1&rCy3_HNfBAX(1XsY*<f+FhNah3Spr;S6=0?~xfhfr_P$|Jsjd=$Df$n{|Tj&FZH^zT6OKG"
    "D6FV<MSF*HKkt>#{3g<n4)6LJ)X_7bYAvr_KNMJxn3^D#qG31f%yHCpI)CP$1i_9?yi0pfz>)KsodYBvOuCnaxnk"
    "Uir4RSyjWu}5vlV+yjS*%eG@+WwJBDG4shEEuYTL>NYN_zKK+y6CxTU9?B^0FNC7?MCociteNy-IJgLl7Xci?V0F"
    "Wg+zMBanm|=P(v!cJv$(~1er!&sV(LBe>$HOEU7o#NU+OPK0@i>tLQ8lr>o@AB4%tEy95JL~NdTJk-bxmMNUU{8d"
    "X4z%BoGgale)IhKikGRjr~UC&9aej#N2N(kKwlgYLg!G>f)^l0JX+Bd>`vWCPlpC@UoZl~jAe60V|pvDGZ<pDtNI"
    "UKP>{K)5&Q?5(LOjkeng(vSWdBb9ahVZX0EcHA-!L{5qq169>hPbTS1;jj|OkW_J-g&q{sD7=fjxR$X`bI2L}r{h"
    "lC8sEl3iwCM5}Mr6kdIB-&XfSIf)3c_R57PIi{IZARNyhz^C7=imrK&@td67e(<7?X~|an-{&^o7tqe%Q6SPlCrb"
    "*FrP;kteK^wck0W4n*+{oh_a7BJ}&RdMRpTQ4jAIRPO}AO=pytESNvTwH|wLzPFhtYr`c_yv$2}NS+@aBG#1pqIK"
    "l*4*awG~zd~}~LlIivs-;!$K(Z>VxLWY7{<Hoj%}A0chK!fr2-qa{LrXGmA33dAm#LrD6`2%s#UFyXV|B^8%CiL*"
    "&YH-N=+z;=Z2(b<&d+Cei)*OPP?@Rob04+NpUTlBk2FwSjx$FJ;0e;%?(g}cLtCR^ZxAS~+ciSD&8~8FjzZR9Iu<"
    "xmvwsy$Pl3TInIJkne6{~jh`mK|14(#IIeaz4#~r21wkqi`fwtnv$N}q+F`y{Ir(W*<u>E@flwc4~44r*&BbP|Vp"
    "3U>=D4(U19-{9$;xrg?CYkq~_XLzp&jAb>p9;0X)y*NUd7!%T2y19%Nui0EG{bDh7Tc?Nie5Lk!jKZGBT#-^C+~`"
    "9DL5hz@3&?=^i<<uNNVx&maF3dkV+l}q8iiRITmR_WKrxt*)9?_4oo6yHIfP_am`rdxlb_~I5?@xM1;WEx!3@$!!"
    "$w6-%`d!f>x{XsCMRxjILIVN1pq%;{k}T>~?K(0;pmD6<XD4d9Jb3<BaM|LPes{s-9P-8Zc%PsZ8K@|I7k-BH57h"
    "Y&%{oPJwyw5{_d+WH9YAl_LVWutggacq{yLxyrqTjfr%^U$Y{GBf2!Ge%y`Itzb<VB?wcs3}ftY>ab$%{vf-SmIB"
    ";9p^jVqF{nz&E@cKV+iNI1oNY50fQ$9$up6kwD|%Fd@N#k4`_|Y$8IRn<F;3AnjwSENiYl`htLJR9*%y)CUP`^2<"
    "fA(<oHBejfZZbpgwS#c;KtJc4y)KLh4cj_S4**Lnw<zy)8LFq=Xc3isZJvXfs8OVFDv_MYD$72pWHe9g3@hVc_Nm"
    "YH;6dQ736319#<DW$AR|yeXW{w&+X<AdK&TEBSgDh0K73p2T~y#>AmzED?%-b!m<+(a{bVEAmVBUgOP@6AsX-^H1"
    "cqVo};aN)(rw2(kA8>&7KamtM~B`s0|tyDli)y2_f_)pC0&&{^bC=V#R(FdJ97~Qm^tQTGamMOk+2gg2O^0qix_X"
    "7Yv*CXuXsP|4kr=x>AE=jxLj)+Ifn!k&>S%(w#i9L8kCUhzKTN<;%I!1_>s43S~ncDtnHK*<BdPA^`l%^6zBAg_Q"
    "g0g~o&cU@wHfqNjj)VVt%lpUS0rNQ%}7%daTBI*u5I0{_{iDp0{DU_LdFnMQ)P5UJsR|5JCdqZ;{FHWfn=MVuoBQ"
    "0Zb(s8MUIhi}=o2A^_nY&{o~hL?x(d{YOz!$CorVDi>iPm^z+f2*<CXG@47dzVd3v&rVuXY$QOI!S_0JxezK#NSr"
    "}WPXEnkD+@mP{pP_EUGo*K7g>BHbBG-z%CdiqAsvru@TI+r$Fn#=Y9CV+6N&Ke|5sr6pW8oDb<}L33@_f(t{5NsW"
    "=_2PC~Go)yGsPw^nyj!?$}q<O)A^{j1_Ja{N2l-&cQ^Q5J!dAh3LW$PRWaL%}4JEo#wz9Jp;ZKpf7ZFti?ez@g%B"
    "`xRoZO`8Nfb6i-)B)68)!6TOux5_x=Rl|v-MJsDp&6__ZyLW2b5B0OUdS<O`2;cnJdh%N>K+8o4NEF`<*F@5QYEC"
    "%C6Xd%(1x~h)#<*F<wpAO)n4CC}iZI|J#B3av!l&geqwp{nq~k?Bg91OFHfLeZALROVY`emUUBn=xgn;%2qwiQB9"
    "q@6-Tv(r81M4J<8%N-!Thh!9_+$&FKaM8F=-ogc?{D6m#dLg~37qUrp>`BhMdvq2YRT+(^yjhVFt7-!stLyncpt2"
    "P3p5PyTEWb>eyO|$O#<NZX5KrHfdK=Xq&FAibl_%tRtSk?uAj4P7ExJ{QYyU4+Po02Ggo-V5@qaSheEeh|6M6S7x"
    "1*s-8tp@M@M8Cy(X_9Zvmz5+>}^{4HH5s2D2Y+&oA-?C~BDIg_VA$S0y_Pr(Dfc5oC|?YbS{EbD<6KRML&VxVQ$H"
    "6co5chOjkMUu`<dxZG2|=%eFy0_PYVU+FlVEhGW^Jy-FaXJCGX25!~Rdq_=$o)3)$swMGeAIcw!NfUK;wChrBSG3"
    "(=Fvsk!KUNC>e{_WCyCSBf<4KN-kKgTdqc6Ex;gc?|*b)UD+R6F{Y+XPu`d#rIB~TktsmwA+;m!zV8RMs{Bt_W6a"
    "Nw5L9gE+@Hm_k|tT1g^nuWQ?O-U=UH5suzir5-N%wvf45S%`;Lc>$nCM6K!w0Mhqv1D|$6I>KKT*36Z?|xqQ?Djg"
    "JWX`&LCo5;OU#C;nuC5k)pqb<adHd+(^zbM--u>I_-4l!f@v2%dwfuRgX=p`zr+cq<6HGdB@tx2p2IOOyb)PSKg&"
    "H8`#0v6wW3Mc~ab|KZAu)yL!_^&{ySa0C0O`1ao|=6+L>Yw}ch7hEWZ>+NdQ4_M;D9vyT@~WEGKq&j?;ZsDR*gJ_"
    "HFA!NKyZtFKM-%F_p@dRL9OG@F4;MXQEkO|J)&2KFL(Eoox_vRlp9P2bApAMG`BmIAU_$yuxSvU1Zr)nFNYNXW$6"
    "Eq9_mZdPq5sBy~ho)hRilhzJWUelA<|vPxfBmVE|}!Xl|&ft6uVyL|kJah@(^bD*s|^lT{ppmhy+~z5UO~FGLH4h"
    "uyswg4su`iRz<pRnN?de(W9mvc13eGI@Qn{o}5?>8PzQLtn5f8KdzUXsw@*3Dq7&oGHDAZ2GLi=+tYNYyp46sR_T"
    "kq*rItJ}6l8l59+PYsDarcaH#y;AOJ2y}zIARhGv((7!aF|Fhv{MfE%h^QXi85R->KFJ}-Vj4fL>Lpt1WCIk?mTU"
    "F}KOoclT*nSpAe|5CKOL2_c5Jg;LT&R6P7wJNCt!`lV)zRs1>L@(g|E<EEx?a74%F0&Ra?>Ha=0V(gbFHz#KE>f-"
    "lT(F%YFHlYz~_PpFk?Ze?9Ljf*2Z55-Kd3Ur`vP}kRy_}Xxspoy~rq)!HG2`Fea4PlW97oO69?7??KwBIT2x_n$@"
    "W_nVXs$liZD5x&c~*Pz+4`Ud}Jm5n)JU$<iglnC4jS6}(M7P-(*DfBK&V2D&H>?lTw3m7jO!7HL`Fs9psMy%w-@*"
    "aWVJ;}kMcl4ERLqM&5^3S*1dmu~Arn~ak~K1a&irzy=?^#edet?dG+v;JojFxlNCT#!H)YUJxN!iGaQE0)xm6?W}"
    "L(!M){+M;7r4^qX^!8e8~Qm)xZo6?w^#sCg^#F^B-81O|ep~|SlL$`0!UgE>cOJI{H*Tsw{N1ajQ1V9qoHz><(kh"
    ")d>MoKMHa|HAN1}gZgb&H764QcQu@aRNM?M3l>tR2;KyLFS5f(PPiq8e2(77dE2`lcyITmXNDE!3faOLd{!=c>iR"
    "?BU{S>?~5chnvMW8q<4xp&A!D?%>CsKpX_pA>nH26G^X1XMDkzBoqh4Dl%q*d}N6XPy-hD9R8sW<3h>&)A#vYaWZ"
    "mmo*e$Nd%U~%<3XZCx`We1%Hp0dk~I*)qi&yowc!AHgrWkp=KwHqJi)NS9r`CTvI!mG6L#TW>3qx%DO5iwtkt>@g"
    "KxG_T1q~mChh0UElYRlR*j&lV?LR8O#NhR3T;zrs#Z=B9ZK+DF5?W<hu*tM+Bf`B&2hX_d*w&=_g^L7Z=dWYuaEa"
    ">DFB^(@Z^cc79VVFJ^Sj}llPFr89$(P90oQ0&)aPJ)dQQ^KH5uu-u+GE9K^nald6+WEkBe(R-0|;0!!Kp;6F-JD{"
    "lK9$7=Wp9Vnj$->-UkG;ZmT-Y|fLEtdV{_0iG(-tMu7=%CwhoL>RvjMcEh(DVj*R*QO!Si=J=vvfYXPN?*>`xI@1"
    "5k&$UkDM<PLb%|&iU258MJkukiV(Q2L{POJp*sLr-qQzB^?p7rXG%%yg`mYX4hS4@!6)wB8k07ju4f2l^RM-Mz{W"
    "w$BXlPY__XQi>UF0BB^^!<)~`@D-%BWb(N2!hFY(#7E}J;nK6v^4;op<JSE!MP_aGi#t(!X8Q3t@zPXdOf&m`_EM"
    "5C?EC|(}!K&AAb4o^<q?#aeflM0KsSSn$=;~ww0Z*E32wMgnrD6V)l%!OE{amfF6wKjnkau9Pdr_jmv+dJ4h-P_*"
    "Z`(LCCgRWF81h^Lu`FkC7M+wiBod(OxH;2_7;F+6+O|(W+O`|}41<k?o8XvOOD81o+fB5=<2f6@QAsVU_;W6c~oh"
    ")^IpRe(ZDB)L+oG|&Tn>)0hZ4myC5PbP#iLQCT57;;?51MgM2GK$Gpqclmp)w_d8r9z$4i`<Nuf`N7HWbn;@Td~8"
    "EM}=|NdGj~;l<ENBgRsI1LW^d)yU@;7^PVP@n`8xu+Sl7L(^@_T7UZdX|na~>u$}kcu~S7y{rMMhGWjw$`un>tTp"
    "7I5y2);T#7O1Z5SKB9s%-uR^H9t6c+vt6+mio8r*u*`YhwWz21Et$RjrOy`<^3#n8-h25xePq3AiyC|2;jg5&@`*"
    "68n$iAL;aoC_yLcRAF|1u``oBzL=P?3dA3LA0?oPvt-bvK9xlZ|JWI6ct(#S*yp(@sR}MEh6h6J8F24abU-1_!iV"
    "p@HNr7VPng<+^+?QS041*s*oOOIG_p|<e?ifA84hAt;eBJS9~_6p7JnA(RG^}#ajEU)$KUSC@g0`T+tKw5q=WNBh"
    "00I(*WxkRN#(Tpp$~wrmMkKv`=H%-*#c`Fl)H4*!*c@Q1256p07JhWXWsTE-#S7Lk%+?8m>&@^pO4mGln+C3{h5V"
    "$9OAy$XgGkx4$#S408TqIqT3A)(q`44XbuYU>xdkq2XGxv#AN6C29&$%Ppa8RmNnKNgd7UTI`%FTq(>hIl@vZbrp"
    "@;)c7lC0ec5Ok}&7g$Mi_p)W9@dtK+ZBY26H(O7Zp(TXgj0-U*<JzYKKLo~pNx&=?2y0ojVc?iZ<IO=G?30tW)dC"
    "plf!J*gPG_~|+h!(HL?6K%+MO1`~(pwLrCq~JmyW6oLq-jiom@p*@qZ;JWU&y>>-34sP~QQ#~#A;pO)4F{X^$`oJ"
    "B^X#%(OPKQT$4iz+^iM62SXUY(693o%@3HEho1`ySy@!Llt%6|_+<Nh<z1JWzp6vXz`||aEP--N1U8_Y>3XYnAe}"
    "Q!Zn|*z{6L<!y9xK^Paa;cSs7NPSIm$xzn85aKLwn|_kKOJ6C@wzPKBv^u^&~#Vzfs?!_eB!(uiK&)<Th*M9Q_2G"
    "dT$_s?)Qa@tjIpm&APoVbJNJ4*e?fgYZIjc22NPWxmsj5B_d%<4!7aWqXj@ndCH!J%sam5uLqTtk7Eu`<n9vWx<e"
    "=it9hhUPEf~R?w;&0T=UaS-xO^1?kq4oV$uJF<70)Es-w$j*@8Mw)U_Od!ob@<_D9cfPa!z!w~sz{R;u<JW7eh2W"
    "z{9uTqD_#;RCAH2%_8d<kiZ#$q#-Ko!2%d1n$y7ix>uhoIyu~3;{6CpuFkORdH!na0uok35B**B+|wl2sGI!!pm="
    "NvT+V30kqM4DtNI<L3rG9fEG%mI@~zk-G2GoMx4G+a}0V<(o1zN4mX2zNsSW7oiy<MJ{W#qZZy2Geee>pK0CZ^pb"
    "tr2w;v1uYqvI-#j<b3-DXVifSD{H(P21FMTE1+sMZV@KEr5(^c4vJZWin~{8T&nnH|qPdBsvBTmzrLinTNGRn2?P"
    "zfQjX>YHlRF;p*!{v6@$=c{e1g6Rj5mD#wAo<ECz&c6?vtOIjTUiLO3YKR-ua{?O~Q4Pqi#)lU2q2nX;9uZswwps"
    "Bn|NBisy;sDihVgW3>0kk=_5S*=!7UgNvpvS;C*~KzD_}QAzy*A!5!~TTySv+0hc#K-SBjC?RYH1{iD0P5*9SX4Z"
    "6Ew-8Dc7v&#5g95-vTlzI3~@eXz5;-}LQyc9Y#)czeHIj{q1Ff!L_Ta`mOL8go&=?(i<Vi#>50&1F4_<{(Q)CrtG"
    "95u<g(RU#NUt3p#P!=Q&c^<8c;^FJIO|9E(Mx_eMR^-#@xIjfs^a~oZVRoR>FV=sL_Ot;&>??KV1nE+{;p9;6VuD"
    "W@&{rV)RYf^v(?;rXim(ekG-_>$JUHgd+0L#fjP4!2o*{ym-Ln`!J>696a;{om)e$TRx>z3AOM!gH7>5UaJSElc?"
    "fMN$RTwv%XB*XWabEFBamhbY3k`cKMkFSYg^F!Uyj${_Hg%e*chtxdS`DRK1D8<x(KRhF6rFBFdhu0JC$pWVqlp^"
    "WBTNWN_BESg>@_`w*i3>2(jF2;QyA{z9s0-G_lCH_6vuflCVs@oe4Z|LbxqSA<5b{}odRf88?TJOms$nnJ>C>;Dq"
    "ZiJX8tSMMXR)U~d*u=+UJp|MJWI2`#)fq*LZ{n5iU|aO9&uFAU>|<PgbyWbpKkDlS{FWz14%=}h|x93{si8&wgW$"
    "~bLgz4!3W(>_5&X$_wj(eTkeMP5x;{Z?Hl+4d(Ll%CTv)x6El|~cUq#Prff2#ctUie(RGqjRy*31CPA*Y=raEu!q"
    "T13)LM(_5NT^d;(t3W*8(Or6pvKim3@OA+U<k*ilC)X*j86j!a&$iR3SMjhoShmmP7Wo>!O%J0FuPm_jliW$sAw|"
    "D)TGYE**-}@1N}bxOZ?GN9O10?(r)>k%jNlKk#bIR2V%@2KeDV<^ucaRH{2G1FKGzu=wNg_NxT5Ap^yxE--vqBG)"
    "_EFeUroCz|36{YX3bpXu@@o981Z+!(Bxgm8p&L_#0L8tdR>n*Czl&r8Ku^M#+*1f9fMR?rpsglYuzP5!A9z;vtK7"
    "N8I^ZX=&a>kV<w_L?h2W;w^uGz*P_(v7ib0W4l#Cb)isHWe^Tu&XoIHRUNjMHIjq@dqm~`#(pIR>UZHJ*p}51i|g"
    "Kkqax0iJvQ?!QlZW(QRlE&3bcBj)VG-SeaOkya4m#h(=bl5!_?mLYKPtU4ZOZme)0PNScTvxLurifU!gE+0Ir?8z"
    "3d+)6j>PYC-1U#({jfmgacJBv0{mkGqY=MVh5(?;z@IygvB(;PBUjjd<f^_u%E;!H*l=h60gTsUuhqNYRw;{GgGB"
    "n|6wmQR9UP>X?Txoi!Jna?^)G|ARzdv7qb#5B)7U*xh}3Vui=wuSGLoMB7s}J8bH+0xl7~gix&Bk-Jz}{|2xM^ik"
    "Bb2xkddU?l0U#80G3x>UkOKRTSNGakTCz_kV@(ey65&L-o2Z5=r|qE>Nz&!$HbzIr*9lc#wp)@j~mpDn6tHS#`(2"
    "ex=_m7io?&qwHg++dv+-&l*sx?UYG4yeUDjEjTOSi==HPHV`&q1G5t+$W+f*y1f|>OyUjcj4PBW4Bxo2S1K0bYQP"
    "0-qi<o+&D+Ah;$v|Y)h2u6JuK<4A(+imp@q<tZm5Xi)g>N0=!(n?YPL$O-H6b^%fL>0kqYd86hx9+U#haVW3z#2^"
    "HWWY36gtEP?*lOC|#O!N4A|r9gz{&T0sNZ}iVE0l@m}?z+Q-WAs#=p}%fJayzD9EC53p?Nriu<LHb;1^s!x8Anea"
    "KbAL9)6;##Q+%tHdFk-z$Z|qd#vqCQ`4kp-_|%k$fkLBhGXIt*Qp>woX_f85aD`V?EPx1Mg75*<?@bHr4ht=0^9}"
    "%#VL_M@lYBt@Nfpfv>S_bk))F!eVSO6<yW_y6lOZCGB)|6!eM=Fh5*%j3w~sEC`DBdaAvq<B_LrkOC94EL1-Lagg"
    "Emwj$L_(%sn0<!ydocEsxQ@KyF8R(w^j<E$(jh5Qk@|AYKwM=XXUOJ0vgH#q=?I^c~-}k1sZL*DYRW{6J8_FQKDl"
    ")lVW@31NYHmTe&XI#J~&U>8soluUIt;lYLO3-jN^azc_Kzq?6{OY>h-y<MgS%Vq4s6?pk*2@B=|Z>{+~eM?RwXZN"
    "&+uV8~G$AL}>@|Fg_*bp@~3JL$gV_(xZ<0w|hg?LcqYf@QSq;#9=1aONX4)v39hOi;xtAvl*Ddg-_avTZbCBS++Y"
    "YSk#;E!`2G{QSE2%l5(E{{HsLDWasLa6z?atE!MmVv=9QjK`f`sC~LrL!>&suTOU(%VK3-ZoL*P?s)47PI0)zUnN"
    "AWXkNgV(Ui>Ws>CA$c_HNjWaXL%15kqm_<NLSKF_K%$YzUZ?<HAkwOu%}yVvIP>Z4f3X&t(Mm)))ThIV4D^%gs2!"
    "ql_1;^mZUW3BT+@)fT85{Lh*?q04vK#Zwc^DR@!Wv$mFtg%uX(3#e+o^P(&mI&$5qr~}O8&5Zr&6TZaz>lVuRy88"
    "w{WTREpFdmK4Jy7kUV2Ps6;Cv$>{=^FiC@T$A6n;;5K12Q?#*b{<6QfPHo=+sJuPrOs1=<W+8ZG}@WUwpO$R;76>"
    "Vx~tC<o!F3k8NJ;EPx4qda{Q%t}JO7U_JgQ~c86a@1vZx{k5|KIGr30oUiwkY~ns-1f;k}VW)5_clE;zK}AbArJQ"
    "xRYGlPZUxCI@Um|Boo?)|Nhpvr`lC2Vce(R_r3HGRKu>l*Is+g!=*GupQL~AAI0)0?~ANH`vaTbj26k!c$`jBtB2"
    "&-0#gv4C*d&E0f=idUyQQxu!QTw`+a#MZ%EzgF8{k;p*9JLaErC|bh6jR&BQ#CSZX3X0WHN84AZhQ3;Cwp;G%n#Y"
    "P(AFE9$Ses!|)g8n49Wcj&9v0p&g=+pcei0K}0Q@~1S<q=MHj)t}h|6}y$Zqz#-tOi{J$BNe(;2vSADK3!z}oQvq"
    "6Q22(KPt)&$!fmy>&LkUT{OXcobIyVV)}I_KT#E+=2WTa1S`!BGV6<5m2<rdyHr@Q^d;Gtx%^&)k?>}v|o_%xozY"
    "Iwcw5fi7XY>EU+iiS(yY=i_=XI2k=S$v2e~ig!+8<}r%f(f9yG2!J<=6MyKRh*-5cWPxd3`AW&hKk$u?vzsxc!hf"
    "&i1pWYx<CY&Ea{+Y!x1X+^nu;0oCG;74mmJTh0gkBd9{hC*?@{|8ZxbtauKei;q-Ws^{osL5t&n^@mYT<u2Q9g?7"
    "KG1;rWwYBWrUCI>7@Fey*bjSi3~0J`thv;Nlfsc{~Y_u=+;+fNI3@l$w@deek&@_g|2Q@!ol|02N!QcK@~50NP{9"
    "86KEFV+cJCq`Sd*y;pm8y6=oF?4UbbX0ttyjY35=5W9+H5NDf;<mM7_hwL0TG9b@mQ-;S0Lw;boCTL3PCm_NH*dG"
    "zySY^Q&fV$&4w;S%<3W0z0$ScC<j>27&jCDh>@|m5$%YZ?OgtrXOT5*1859d4?k?;w(p_M+6$K<NyZgceBVCKP2p"
    "cTtIptK<nAiT{N$>bH**`ozicijbkd70dCO!-;NfK)og7Dux`uonoo8C#%c+ryo6tik74{FOztZl|qT+y71fq%5x"
    "HgJapU;$PtH4ivEWL3l;H$A1*x9#fNf&f8xPW<PSK_QBS)V0{CNsX6u<K)A+-jyZql6||lG9}g~EWHM)4o%Y{3(b"
    ");JIJroWQi#IV=!J0vt%|#zxia6&aq1f@okoMv{jgC6~Z*0s%trY74omyZV02!JsS|V0L`B>WtXICPy;crkmKrLd"
    "iWKp_Ka4{F&j~47fC9tLORiMOU86ejncK}$B^VpChf)69_!G`8b@fahlQ`#rHyMI>HD5!VCplf1R%R>KBiZii9M^"
    "^v7>x+nCu=MzC769J+-`S?<f(9hO|q^>gpd)w#$!u*=cqUEBXyfP9&oK41_DP-PAgScaD_f5;m=qT7HHA!REJai<"
    "DOKm?WstWI54(bWgXWEe}axe%lgl&MNU2+gK7`UdKOytJM<((851L!*zu5<3W<9FErow09JAV2e+ZcRgK$hc9Z)V"
    "%8~5kH8YdltmIM-QFS(o2)9C#sE<}|D_dR>LcoRi4BL0+19D$byCsl27@+@$0NUUu7@OWFPhfTlWg+o(G1$Lv#$f"
    "LIDuIv#AaFd;D?el)jdP$bT<9c?O@Ah>L@rRT(q{8*N08>dE3c<R31$y^1G^1anCu;64<#&FVe#p5IZi>S8I3{oe"
    "tmSZ|66h~PA@V1>0$|3nBPvuqv;1`1~2zt9wq1q&O`b8n%e;O<?%+dE;{q)S?}h22AoO}yLnO+u6)!#-a9%x_&xd"
    "W1b83lSM$a!$FqLaKRkMQbZ~I=D<06TX7qtW%KhU9w11NuMa%IA*PM$EU!&YsPEw&cG=p?Vc;sS857{?~+gB#TN@"
    "t=Wf8zob{f4B*;`*mEFMipJ+)5Yilm7n6aqs7bj?&J7z5_3$jur03eDu!@wUKB2Z@&LFT5|6Jwx&G6m%ghJ3laq("
    "K@bR;4F9M`6dVRk7`3LuVoAnLSBv??1t`Rn0UB7-HP5r#8K6C$BaX^3YnH=Iorm=x`bjq~GYQTmnJ%<nIRPy=!&>"
    "iE@_XocsXYgjW<-rW{Qln9On8`y>e_UAxDsc|odKx#I2xQ9_fQy73S385)F}jHpUr9_4YB+~#9b^XBn^es-AO(2v"
    "W+})??lP^?ZGr`Vmw4e@lRcySq=4&HbFkd(knoUQ%aumo`WPh&2AFoO1hW0c66NV|9p4^00{&)23CW4sw5oA>|1J"
    "#2(+x`8t`i=C|YWkY;%el9UCl2$G)ei_N6>cbFJhcg!zZ|ED-)v30{_s_)kLcR?=>_ji4m<qA9zH6O16pHRthi2}"
    "dAe3t7xaE4MkBnr-NDtD^A3C4nDC`l;Ba%2S|njjcz+vPPLKV-hBVO>-ltV4+TfHg_w%-P59|42Br7VS0g*$kX@D"
    "P>gbfY7L3-a_c-&7?@dGMayZ>5LAOS+_soB#rG|zGaz-zeBbg+p;+8AM}w$IBO<G)j{C<osq>ti%A$SPnUjz;_(;"
    "bfQH>OVhoFN=L#!e~?!<0bpmf-{4L5}=5o<@T02bA}4{4eBJh<+Ag3hAJH5tM#=VB+zm!nwE>MCYs@n=iRPU+E9?"
    "&PH_BaP;cc+MV~rBSS&f6pz(ox91+G`59M2_r;?z_Y7_P&|GJVWI*9_4)zO(W=R!PXhNvvdGxbIwHr0un)^I3a4D"
    "8J%9T^z|NQFsE)`=N#4VT($Y1W%_r#3@Ow$i<D5L1H<~M?bGrig7Y&IKlW0^o6LJxP=5{ap^H<cdRq#%Lfva#BtO"
    "6NeH(M_9(U9{r$gm{omcyA_Rr4#;!3^*hJI-pibthGSiku=*x76khj(RiaR^)>ZZNJ8M6g&T9Q`w^;#OrL1Rqo(x"
    "rq(+1E)g)LcY}{T!zBel*_o~sC5qN$At@0<vSVi=iqiZ{yLItP+xMYlRo0(kiA&cO#D`gV&QQ!iq1DyNQa2J0qB!"
    "AfM~}u`nP?;TEsqm(XAPqfhpWqv$I`M4Lx%%~MEZpkl~!94>ngSFNx=EhjN}YNR;B*dx8L`_`}4Ev<35@aoz|5}*"
    "=y^U#FBj|FcqyR>+-+P7lfLT@&`3Jj-F>ApNu)`GHqJADq9pr<r4_n>-Wa{08%T5yE7G0!L_1GUZm7Q*`sCk7wUA"
    ">;}=|)^QyP{ws1utau&ym3!SB3V61RHAVx5{T&%O<l*$OXChZf}hk<?i<ig(?8p(G17`|}lVzO%vrnE=3AoC$sT6"
    "s0XP@>y)M8DCn#bZ<zp^RBNwN};M(P7W8ZpRhvw9T@yxoZ{Gh8DWhJK-loS3od$Fqvj+s~P#ctY-ftIXpT|4&NLc"
    "#7k+m$YbT!kNnm{f9v#6pF+zMaUGwqt9W2SP@WANvLo(^tvIcpVl~1XEJ<@|CKx-Q79$lyN5eRFqTPyoQua~C0W2"
    "WX`EL7Z*-PjQ!^*e>Tl=#9hL@iLNsqsc_O&@@^+a+7iwq8=7m}bmQT`GTd~NPVuyws+MpT67AM21UdhUHyJ8|=(+"
    "d|xDVPTC685|8z`Z7Q9Rq~%FM~A>x(+SE?C=U`>%%(7PU^mxB7|Ywqo@s+hIu46{Wc0*j-Qle5v46)(P^^1qI-lm"
    "ZIX0_{BwkpG`|i>2vn55#QPNH_NvCK!!g+vTdEHLlU=eBRMM$yR6s^tOw?LwvWQ)<D9r2MIvqK1_M-W3e(3|)ov2"
    "wIlDbq1obOss#j2QuHFiuAkw4G35N#rXxAi-Y)?gQnAFQJGJ!Z?V~B*)Gtqz_QQa68%M9<{O9o*dI4>DXqGZ_LK{"
    "Z5R<xHg`hB@GV*gDHYbz(|HHd7<ykEgi`eII&iey?Q=G4nRA4!w?lkH^_};1f(xaHq#s)d63nKCFC`k=+|s`3us_"
    "nRutmFNOAeU2X4%CBEG7RU(S;L=`diW56;X+z>@wTHQZJQ-47QTj^BExRY+M=#7%)AJQbgoyNf3v&IR4i}68?u-R"
    "fA=6jRlktL$9r5C+LS6%JJe%vRx&uUl@bVrPEie&!j%Mr6ClkXY~7kK#M-6+4cK~-4|i}hU*oA+ihD62fGeq*LJ$"
    ">%qZ;H9^OX+ytUdSZa+i@*jYYe)mFfj03{f6&HZ=}tAHunsYapWPC9U+IbG+=-#2%ig*wczMwc`ll{GjrHB;q?i_"
    "wCO5je1}nilJXscLIRJstYN(J%wFBp(D>7Ip9c14##*gj<UW+B(f*0pME)&E*v@;n@ZvZQr5n0q-q*Y&@G`#YlXr"
    "r6uJ>gAL4|C>Dr`R7TM;2-wjfS|*OO6O0rY+{{fQH1N$Vs%Rtq=qTmLKP*j{MoNI914TMFm)W(E8<+#PDTz~}T_Y"
    "@wGEKOs!-U7hL~iH<61uS>cEcPH%n7-i1FEQx)r|95QJg;IY}jWQPX5`W!V1U;(S(K72xr&DzHuccEKS!PnmS0xY"
    "XB@N8&KY{2FHh|o?C)&BNrCE+zWr|(mvLkh~cio5wOa+#G~O+WX1x**aiw4(ln;&Hb$5YK}jufVm>m86AI$2Hpv?"
    "%cI(4ZgS9>^Tg_6BqkgD%XTat3!*q5t)fWTPAGvy*iqi5FS~uR}yCY0=$hB$cBVY6;q{iDJLeseQXucYWbbGm(y{"
    "-}m3gOH<6e|RaX`5(*SQg}EJrH<b|BmEg2dnMS_lsG$wohho@{4jhot?q0bS*jAEA0$Ry2?;DgGEnWY>R?>`X91e"
    "?aeK5j=(Cr+}RpM&JOlBbwjV>p1cOrE{Zi$c~?GP>D6P62tB7cdl^RTdqS;(qAW9%Q0)$Z<VlxNI=h@=(os9vq2e"
    "9qRAay$l@s)gDqw5grGQna%9!)l;y8S{Jcsj+ClvS`<y9s7d+n0OR;C@=cMbaUaOYL;<n_)jwW(%`hHYq`Fd*UIy"
    "m|tJhxPS+w%aRP0nmYWT2eLRF$aZ~X{19s%L5P|Q|c&D$|=Pq7%L5{XQ=B_sBuotA}80#Ib86{Y?-eWiea0faI=t"
    "_?LgEVBux{<HigLFr-Yip!lM7i|H9sn8_ih!hU^=0>qy8(G4dbXT49;b8@F7G6qS{-X?(P#ni~JWVAcKOS6ak&uX"
    "nJI1sSpCNMQOSXs(h83v4KAgOP*^C5)`fvAB4S=Y>m<J*R*XbBw0cw*W7(@u{?gd1Tt1LYP<xC(V)o5FGEklo~KQ"
    "uU{V@{hfdjZ}AbSkQW)7N}bxV9=KbG(I_~!nDuAr$Lasvd|^-Pc6r|po<1J{G~KOe-cfu0k-5ux@_QHj{Rq1bXh$"
    "C7Ff$~^H7hnN8@E*W$zr}TnoZl7U({J<x`MbL=AtFzbU<a5{bqc3rIUJqNGI){6ut+Pw<YwaWr&U6`A96zE#{fE5"
    ">ZM5rQF7YhG+@jZJAgZBe_3j*~4r9CR#_cGN;3S$BCcuS`<YBXY5OEtPD>o7Cl1=f9?$~RMrVh8#X3}QwX`5MPRX"
    "DH5HQzv0{?kRT-;e6x~7;4d>+D$f)rk8%IQ*Qe=(W{D^EEH-7jBT<~=^GfgAo;%uuGGqug3D<57`BCVE7>jAxxB9"
    "Rp1e1RsJtRcW^s$z&!{ELDRg=)O;B%w_In$w^O@Cc*;Vu52=@G!k~r^3aLg{bp>TGLPAOGV|$)aej7kx>I(0QXcs"
    "*=D?sDDwEB<gF^J5>HEzreHUsyFl@@t_DSP$d9sTYjf0AQYMz%l@2Z}!BgFubwf)OfsE&4f*uYEh8&MBN2mn&Lcg"
    "c0^%WyHmddZGNCN#@A-|NRRZR78{G4Wob@4*n1Fl!P)A;yXt!hOus|hGGH=2wj7GI+69c3>CV`#W2?thi!dB<hO1"
    "8%L<sj&a17Ht`(l6hAiYFndW=|F9@79vLL)R`gO2e~4mj`dhjy)ltqjlaiWBf^0YksJkP=C&4axtxn+&RShDa9b8"
    ")M7QKerG0UedOd^)RAF9;A&^moc!-E@VZJEWP+EZ+x>ZKmj!Gu7UdN1GmO>{XK-EUB0u?sWwkt`;520k-N~DmzJm"
    "kK}NjI`#(UU~_gAh?ugwd(ntjIEy-PS{!W0K5bd@DPPra!4MhRuJtNSs>a{dhi}Gfv_fqgvEp2CUlL@l^}HX_odQ"
    "73K7|#=Pn5CP~u8EnA<u50;bVI4$$AP=5Mn=b+bDw4MZtR?<+&wC<g-T0?i*-8t#uhY!8t=~^<qWy+|>B>z+Awc_"
    "300gSw%%zGn&A#DTI^V{x=pq(mQC=Oy8bCM+4ec>~@;2cXwM-dfCba-=m^lImHf0w(kSkfmgSG02k!rMwkb@FG|N"
    "OorxQ5PFab2r+e-<(}#DAUo1D~ZnL(utDu;VcWptNJ6zd$&1_(h<{j`h?04#Z+1ar$o02^^1Q)37V4${-@>VAbUU"
    "~k5nv;+BRKUy+7T&0BQ4T@wK`#m~wD@0+y9QkpWBKCv=dw7^I3nVi}`)P?L5zu{CT?_qEqNq^)VCo$1TlnCc<J!_"
    "sPF)@qed?d}G#`i(LoZD&tZS!gy;<Vt$#F6|yA1(@y`L~m74I-jb!<phd4RFL!LP#`JmUmiqSdd~IDY5|RXANU}3"
    "yIXR%J3Q0yJxbK3Mp*gs;$rj%e68)eY$<WKPZ91-&6DJjsFtZu2ul64^iiTBY)CBha8waZ>iXWAs0jil){Gm6<ew"
    "7cDbPq_&FX{{7>EmyL!gIdwWRBsLSyBnG|-JpiJNc-Og{#2xmG<#IdhzaAsKZ?bJX)Se2J1-(4VH$F4^XyXW&m=8"
    ";L3(d0(prl|!Pr&vIa8Kr+sH)JQ_<oQyPYc}l{Yjsaz7cenTYRIMh*z5fKn54{pqlbS6TgW1I7K4Jfw@iM1MlwM+"
    "7M1L>$50y{FuE`tlPo8sLS*MgxB^SMUwnoNr2yi-sDPlI4OVl`FU3}2$T9P^kQck~QPUX<Cn^R)ps3Rhg_3b7V0c"
    "i+o5yp*>4;oXq<Z&}|?y*UZ^%#7a<r`E9Pjxi@z6Q5^(UOmqOY98~Pgr`CsfuuJ5v7%Q{R_A`dQ4((-fscxh$t;T"
    "V&74AyUyQFN=2E12$KXCilEpEmRF*Pl<{9_J+*=b+a3}TJh}6}Z!)+T=Pi5T^V6sZDJ!TNYqOj$6TtQGngY4=jdM"
    "Q~71aZ_QhyMG&|KXz4*V@QCmb@c^wd2P{y*RERkBTiSIh|tG+E|cxZ1r|-*;Ay1wqwItObf%qQj<=klJgQemYIk^"
    "BnD^9HMEWHkID6yJ$2=$#syPV;TMNjBH_}+=gK$>B3XAu%QZ8bi+th3E&*3w-nMx87p}^Ii(_-a~M4jd!i|vB)W%"
    "FYvDR25JU>B{fm@sanR}P+F022y3y3an|hs!c5ZE{Ro!bCBe18AG4*N}nT^xoIa^~Y!jLj=Ou_i9@Xkv2%)hbeAm"
    "UoHH;qFAZ_0VBXAUJ=vE;<>F#3}rZ(S<BJW59&$D2}I;%5qlkrqc4lrD(Z*J*Ut4eE%Q1&XYcgN&l4iPBuv7{4uh"
    "Hn8rMJ!abhbS&j4dss1|Bj`~2V8PrN$qxN8<`(iA`o@->z27%l>Bn?LrAhkf1?+5hD~Yx6)JQtRbzMs~6(z&appD"
    "&~!(BM5dmGIv(~|2kEnlpc!*1EFzvy+upklZOSz+UxaW!MyQT;!2^PnVN6$r|3l<V#D40H!1vA39Tl8?A1n5#<|2"
    "5BNujL&g!i=z=~Rwv~!1;KSLsuh+nXNIPE6fg-OEl9FC1rjL?HA|<SCR~KfsX@_BUNQ$5%4D9aqY4&?@vdn?tX!C"
    "Egj23rQ09RJyH(|6YHNJw8J670xfD|n5^R+{U*7c=?TNfbIrZ2@!P8x1c7`VmsSryV=O60)D8@-Vs1f1wRrI>*d9"
    "gvbiX{#hB?ZV)Q;T7r@|MV8k&Fgc;5YgeZ)VF=;fg$QjrNH0g`k(97xn8{<U-w%-1|nH(nRUIVm4hd+~Qw1k1wM*"
    "$|L{NvZAfjJ@;Z*zIea_xt-RlTqwm9^5vw#Mh_~4uwK->%i@iTxfSzUdo`fSntd0e+yroC!9x`x4Syk+l)te?c!W"
    "O)2S}_D645M7Lh$3QX_APZc*isus*x)PP|v)vC7PpJcr_vlt{lzr-xuGePT_WhngL9uGF|<!5kB$ekQgry`(=!4m"
    "I`i7$s05nh5C}lv#xV=^quMeK$1^1Ag{Ycq(tMb>*$>Nm8t~0nh}5knSW{_PY~6HB~XyRR-DRWw6I|*l9t;nkKdC"
    "gC@-(@l+I++i;(_HxA6M<2xCMfEbt8QS&pgtf0h~aO|WarJii)UugK`O=pOSb+%Hhpju{J;)x#U1929II4$v)vl>"
    "@r_pDVI8a3@w9@)*r{uUEJ&;>%YyQN?lZS2~Ri1!^CuvbSGmQ%8=W18Of7i^}){XGGZKTyggs1qs-3P&SLo>^jnA"
    "P04Z{k!wA%>w$wiR9Z-)mIRA1amztToJ8Daa1YV;&Nb*$_l>B9A>vz+`Y`K+b*(lo9CH#k*(6QdDJ{Exu>_@D`(r"
    "-0CPVgUQHcj_MzWxikpE*wZQJl7uxgtd(okwel8GrgpsThc<19YQL|u|?s{(<9gRB|M;#Xr`VG_m$k3-lDq<ypbt"
    "qn9$zv4(LLbDl(@l&gHd{$m<K`RmXj!e53mg??nTQAS^)H}oyO?5jmk=P?utLA?yrV!+720hSXW}E47z=6pj7jDt"
    "4qZS7?k+LY#C7R}_pLRhn|2Ot>crhTJIjC;(j#EU-<SdyoyDRY36j`WbqV|pD^)QtZYPCcC?4d$dG@JIZ`DR!C{U"
    "jC*&FIplByp}*jK48GT;AGfnb(^^U5zm3L6-5>tqt+smX)cvPGu(EmqY}@b_y)o056V3gALqX9i3y&ho*Q-2^5$1"
    ";BxPoG!mqWIK-q*CpBLb5*pCbAnY=rt?sb)FhTqqh7!~aPkpeccI^fhiE5wT*A?bb-Hrq9sE=-y$IP#NQnFJ)Nyp"
    "ND44=HvpAu5+K2yEoHRl%4ayMQ0u1--sY+FA`y`p-rMwb%Ku>C^^q@Q#SDu^@@#T8?VUTt>YGU^!DC!1%J*&>S+)"
    "jQe!Ywy*LH1xttyT?65;nSU;4tfzmrJ=DXcu0Fc_l}d-$NR5#j(<;n>HVI-V7tEn9%J$5W-Fm++2pkM+o`FKs$nE"
    "74e1!Bdg@;9<<6UfQ&jq!&)-es^g!l<nPc<?H)kxt+Qsw6RrW`N>#dxRXXlOWXHEF$dFkrN5Mq}`Gj`V10;V*&1S"
    "!{BO7iA#|8H-4re<q=p;S*XxTPjhe>h#cdQ^D;t7uk0tHo9c8qg%wBruLnLyOVkC1)PuwddEc0{b)@m(7a&eH%8$"
    "XmpK+va+W)T2_cEdE~V!YEx%t_7C@ZzXdzfX94W!Fu2~3S}wY}iVe0s7<HTT>>p7SMl<IAAq?}XcX--T=V7ph<K9"
    "akAcwnvbHS8GruJsV#<h|OpbS<%^@jBT5w76BKy9l;(Kr^y5m1{gFVOxu?sG+>yog|Op2O#Uv|)}@tiC*4W+7%}Q"
    ";Y?uIN{rhnYFO42EtWB&#k{&O~QixuR7b*em4L&x0?u$J6C*<jZtzirBOmT^t{zFAu605yJ%Zc)H_76#<tvc)2l;"
    "|)Vv(DQn<cR0TXFz5nR@OFfp)1A+{1KTk^KEpM`b{tHH))>ea;Q0nBMbwGN0x3amQ4_op*P0SbU6(PkkCx$afTNt"
    "e6M`L5<voXONm91oQ+6W{XevLdluS8_A8nF?cyosr7pZu~uKi7Sqmu1K;?cOA#=SGfkqceql{DHFPwHuj~3b;F~T"
    "zI<|V0ZL}!J2<wL^;FvHKiyg_@D0<^_|`JZC~q02w`G7587*IZSWR9;6)?H61x69o7!jjeCWtXkfyBzuU3#H(5Z2"
    "bLwK*V&=a#EfY>|=BTsG;5Y5{8R9Gt>*OGwGi-d?hMbnxcYp+pLn@=sIoaierhl75{L*Mwi~af1*+f6@0C&-gJPU"
    "~a14R1T$>aJ>IBJ`?OpUqi9_rghW1=}*0vSo}f^14l2D)n&Y7Lp{bLRl#7mpZ5<FvG5)5?4R@+J3k#A1CiViyO|a"
    "~aXUzDG@oMvX$djdc8EbeU}?SDGEuAwRJ3>*zyc~Mz)8PRkoqfuKr_`>;~*$w8R+6b)shQ2+)LJu!^L6ZT1U6x6o"
    "5?0>RBNt*Hi(8_N|t?A6U_=B~tmo?X%FNXb?!H;Z8K<F_pMviQNi;%dr^BHtGp2Y-U`>;`2sQmg6FdNvdj9Q_;sk"
    "2U8!fMA|a<9eK+Pmo8#VA$ESBu6=%~^mWO8VlnLctl}KxVUV->(F3s#MZhUlkpsNn3ceQL4b5#8ZJ?#2MNG!>d)X"
    "GLM0~cO5vLz2=gS78mP!-S`Q{!I=1;9h%cMrROU69?VkP>ADn^Q`P*FXR(_UwYVU`Z5)n%aQI)YuF<nJ<p(h*A1@"
    "wiM%mjJzLA-<k4=?i}aJg_jXWcP;GD+pT(iB@6ht=Jk{?ur5ga`(9ck8DwE6Y9T)c<{|i^1`ZuCz!$P<GX43&{nx"
    "{RvZxJ(A5L3F`~500yZ<b9%qXxQ%i-+AQ2ON?94pEkpG68Tp1A@wB$pm29TjVoI<7gp+zJ5^QArIj=|mg?DaUE_D"
    "c)`(HR-j0%k1D`|<gq35TJ#4!inxweDHy%@$Kby#<>3;j7MbeQm&PD|b(|fDV5+Ru$I>pS=&m&<>Vn?)8uQcPo#2"
    "QT_Czfy)E{4cY==v7yO-i(<p|nbwAu`hq`ARPjc$456N_MyPp)&5zbI{YLoaT6VdZ<qZ304{zg!;FwTeYWFr=wVs"
    "Q`x2RP*Tm)2owV-(jC^yv*Wqmvt(N^xT)7O+4ir)rd(bA#JLR&g!6Sg=k+ix-w*mKp|_!Ut;qnIw+k&VCC-e^{g{"
    "%%^)gVM=Zpw5%6SZ-o#Lo=H;DkTM;O<kivC2XR*QK=B~GuA9Xf%sy0Usv?ig-j`bW#=Ul2rctj)Y7Ts)nV_~_WID"
    "26)}!KFiPQ&>Mq9F!Mk>n7QgUXO&s$B67WTx01u**z+Yw}0Oxwp#@PA%N}%nSM|i&Cz<pToQ#dUWliqLpC#NS$HO"
    "m@>C~-B>EKX>OyfaDvK+0JCrsiq#u1HR%8`|rv2Cw2?cki)b@1_rqVE>bNg{XuNlxJ!y(sd0#uzST*t&NR_;e_~T"
    "Zp0~+!A3-n`yz$>t-Due#qOE&7cGM+(Tj^a<aBq0ongia(be*x3L`b5e6sn+(I5+YXG(hZ)hw45Im6`SZwJ_-6{|"
    "-sxc%qz#6<ksq$U^@LC4WG_iddy%gvv2+Zi+e#~5btjs3km2N7<N<@V|P*8aW7Cf66EakjF}Cf4E`kIr>Uuc<X>y"
    "t`&;PtEd<m>P?Jm8IjwRk0#rG<2RyjO2dTF7BevJwmqMN1M^C%3JrMa}8Yp-K+7q8O;;>`S|F~YiuR0(QAcJHwh2"
    "MuCdfTt9I%<W+!UYOj1t}lBlGO<2Q$goVTfL#N=&8b2ek)cv_H=+i4U+8QWhZklulw7pTYWhB~tCen=nzR(uv5{D"
    "MzzQ5|mvy4R5dN!pedOPXxTgZ?*7p$F6NrL!LXlp&56<n3;s)vh!_rYhaGWU|(-{$LaK$-Qbp2m8PDl8pu0x8~`j"
    "^S@)&Qc(slwEg~TbTW3%(*YI%@Kbf1VhJ50PeeHI4_i#xd8SS6uX0XNaj%c^ettU{kES0Q#o|gYfmHVBMN?sk=Hi"
    "uV&`bpWf{CqmKf-3l_T<BGG;i<^EuBek^=BWny)PFm?){-PxQHC!XC~<fpnk*IlFEyqbqS@CizPMp<7^z$7%7=u*"
    "osqTIuvL(!#bj~98-d(4QGxmym-_nNhA4h{?Yqw_dx&t_4w%U;P+OtHG8(TCG&(ERM)Fv2ao33QNE6FD#cCr+myY"
    "NPt)uCY8I9=@UdA?L7y#FgU~w;fqH$s^Yg16>2QjE;K5Zk_)wrjoFp;(5bYEetF^_LV1`X-*yJMRLV?XNhtEL=g8"
    "jQk^K+~>ic4R>CQpLT0&p+#+v%XeciYIer?W=W&ma5=4nvRr^wXZ)&n>5f-jv)iy$o>8tj=Q#&g)(&Jd|vLgUB&q"
    "&KY!4o>|m+jjVx-m~d3q&?ek*>rSk{i~R<#sL^`f!iT3oo33xMkvqZ_i<;@yYB8N(vh11*$YFGwl{TicVb+o3fT9"
    "XMg7S<c4(AwkI;8Je%#x&bJkD6<XPBX(h1)pXU`tUvbozz1%6)<Ya`3n*qG<6l9;UU;<?)Rii}QTQv4y3`Xohx}X"
    "q&~%uRT6VQG6VY#~QyQc5#jzAK$9HiR<Lzd{pm_s@zC@pV1;-{f;+IOL75a>~>8RW_wZFyzs+7EfEhJ%~ctFQV}>"
    "yOxr;{FJ<|BA$_=b_vlkN#dezam-A7hdG`X{G~M|OGc@1|V{{1_`7&f7vTQjZ8YVeHY?#lN*M8js33?<+mgQGhT#"
    "d|BShdD$5~t=wg#JX650LNp)nd$N{zTiFa<7uUUT!q&ug7F8n#0DQ*Ka&ecpg}!fDY}&XdX1({VI7qN0i8<O0Z@{"
    "PB7eBGRcO3Da-jeDOXG=NcL+7lvH(?_9<4tnWyvHy%9Dgoy~6>7&<%pqx<fW(M2}pTbn{_7y43|v`91Q5*cflhnm"
    "UPiA~~cGmeHb54&NU_ORbJf|jqPNKRj+d0jJjh7smtP(rw$KH4lks<+nfXQ`4p>glwg?u!=7^lmFiZmUA~Tg{dID"
    "L-#U#%y2%ZMyc)C)+Iw-RqLwT>|#_N37C`n{O1U{jb_nqP6}}sR}Fo$HtAU_^adySc^^c8KhJ0uc}pq(H*|1D)7;"
    "+1IC)|4uTFbTZP0}Z*<@<z=#@=N7gMwuwI1;7yF`E7n#u{oqwRJ_%&Jw#0r90X}K$7@dy}3-jE9vH;?_C+uY-t@|"
    "sG3<BX^h-XB#0o;ltu-=Ub1HOju=Ja_?`!BwN=nH5rF@Tg3=;Y__Hu&BZkqmVhGxlvvAOm}XOou)IVV-OlxCm@-*"
    "g?qVDusIu^@UxNYnBon03IuD;9G;mB6Teew6|TgxB?)%+d{KcAE6q}?c4{UupMkhQguf;ACsEwfD~~B3D@*5tE5F"
    "Ss3A+I1j#f#;kJ|UCj4KdrBfPjb?Nwc3ewzc=8B)qFP_uMOync>ZgTxqN<qNI`m|tZe)%{~RL$RuDrQpR9<-l}o!"
    "6t3TSbro5c<60TI!B=ceqAXDIa8R*QRah`41Iei2W?wiVtU(PU9*j4DyYjsWB%^Z*Kc<=|8Kha&#lcL`t7eb-#<Y"
    "<0kCP{SDQ@|aA*P`;WR=>HLIn`z`h{HSsKnZMorJD^loN6Y1BD!mgLtYnR9s}0qWo?#bBGDpKsH8ma}>PVw_%*13"
    "TH=)a~Eodt7Q?FKVfM9V(lCBoUcj)`!|~HU1h~O6j(zfL*Y#{`L)E>HBxnJyEcc2Oca3w;QNB+@!bpCah<Hoz_Td"
    "x};>H9jf#?%@#OccmTti+ES(xkpJxoLlA~Ny}i!5`3QB2cT@Cxz$iwT>VCqF0->@8J9UC4?CvMKX?Og!gc2_hNbq"
    "dJZ+voKh_6pSj^;B8bV7TI4Eyybg%mt;oRNvVJDYBz{=7s3w_H2P2Hou~m@3zfI$6xF@zM`)>CLM&|Ippq`tzUPO"
    "%G>>+0E<u=pzhx34*|4jvd1B0^s`T<l0;St!c10p~Ke2swEibdJH<)uSkCJ#OG$+0IGdHK>(^>flXz@pKiNAJJRK"
    "NVFBvIJ|JBY{A_UbRjniQ86+lZ3`d>jHg5yjUclL!u$BTFz5K&dRAMbW<otNV!ASTAI0RP<Pk;^24PBa~Q`qo%(C"
    "ruBwbip^NUo)!*6|jZD$T7G%~Ql6piq==n6DB)#-&>Mp3u;o(YCx8KW)KV_F)aETwI9?(7u|HofyUcHdVp6{8~Wq"
    "HNpkP|C(kKLW7F#nbkUr1#~a41Q?^SCY2}_?1sx$FDFU|7ZCcOh2)DqD$2?KNw#KiPFAaY?0q19!lxKV)8m^EVIy"
    "IOM%{Y0wH49zG?1Yi@K_i1Eyj2C54U;<?!cNxQ>{FMuNq@7BC;4X3az6erBh3czP195K})gQn8u!d@e`6pk)ZG=<"
    "!jCp)=k%*FQ*MG2|~y<Sjg$w++-}H@-t~RnV}+!MO3IN2AL`Z7E)BN`*iER<8$P`UdQ(3k2v3S)t5k+@bTU`=bd}"
    "(%6jNh$9{1^md6>H%RXkN?z2n#yq#NbUq<;o0cVh8rD^s{B8q7a5PZabz4~(?W}6lBJuOk*-68wU37T(OC(CpC!>"
    "_~v(j|GlVMf<5DVn0&3*nFAH8cNKte1}G$yBz{5%dfkXQKss7DYa7#cPr<e1L`y;j>!e%zG9v8g<uU<~+{R!Heq@"
    "79r)tjW^g^&Pj`qL<2lBpx0)@O-=jPsv;=(5lKdOC%WAvrSTe>cP8cM?-z1_Rg%n)355WxjzB1jC_wA^V2t$%bN#"
    "Bh^e+iIh(1n5d(4E~N<J*n{fC)j1K$5<Hq`@4*SHyhiey7VDK944xx%?7&IN1B>fkPm0|NKXd5G)*?zo(EMOQSyR"
    "@BdNX0KwpkP4+d(|y9D0}R$@@>r}lsf`azju&|!D7eOU4=^!N@D!-?v@00fB5|qN^(Y6_Z--KGKb!tznJv})=a`L"
    "*O?21Rs?_8#OxAJR9Jx?!6~L<XAFvtY1(3jnAH!>*L#cG8%#aD$a)H_^1$WS}NhIgK0gx}jx5{@%ZUxy>!KVTvgI"
    "~`Ur9TFe*U^#uHJXbRTxW18G4pO?;YPWg5&dd3v3%q9v;H^Ve_MExzf1KUzuPL@mCsB0$HFZ90>rRk&B7y22PD}9"
    "GAI<MY|;>a#9R~aHf5Dr^+dq#=;dB9Ul}jh4{r%8++I^4!2rHnQ_oU}cfsLhoMPSNo;@|3XdvDRDOM&4ZdJWA^y8"
    "hXGRgW7N&tdNg(6?hGm=PG^@yCp%4f_`tb9uIQ!7WBjkC%J!lXs-S&~L=?G;{~$<TGe|4njni&G)P(_BMH)l5PS1"
    ")paWNQD+Nt9OV75vqR$;zM$R3o5@&rS16<omYWJkc7jSD$~Tanez-+9OyhEg`rI4e4p9?HN)P*0>?JTMIu9iFPW$"
    "!vYAhZhE!bxduUA3Kj@F{HaTTSfxP#%xH*E_abL3^B)rNM3d~iZ0a!Mpi|a&!lzjbl^8K@KO{mL?W2*7?$I1TBhn"
    "PeV)=I=gH?N3=TQjjqN7tYm*SK)IRcdrVU2>siK3e9@un;UI-bpwbe^=@?!^ee`#OCAr#u-uz{a8~X`BW09Ki7&_"
    "%W#H%=g_cIRYfc$m-OeEhHX^MLPuONn^t2QhQ@;@`2@fs4TOILiUEwmX>rZgoA0*BD5GG3$DVFEO^9V6c2<O<M96"
    "I-2UN}_s8i_x$w&6bRl3At&CeY<jvL$?Da{)3+~(48_qEAatGl1(g<wAm*@MB}dN^0gzv`XC;Pi1QsrwujDU9ZVw"
    "<P>FlC9$9cC=)VTT1_l{QDmXctI;nBWxDyrWXIx3|jvBK?`L?KxJ+IMV*I#Rn{GLiMR=_C_D-+n*=(co5r#l56?|"
    "wVmPUVil<l@otltw%_sEUp^p1po3NTgM6`igg%HzO%mB6KvzvD8V;GJWe8)ZKA&g`@gJsg@`rU1U%?;tgTTHy_!k"
    "!6kM%*gKJcotVc?F%%D|5?K9)0RcrMmjZlNXA?c~}2<@}j(1P?Sf66@CMT;1g6+o`o4oX@OX`O}*&~=qZnpCcO7l"
    "6(1K=#^k>_ZoKQ_&4VkDfmXLpY=yR(@Ig|<k_RRTZtOfE>5U&^|G5OCc<!7Y%o-!wpU)8Q-R)=v&<`U}iwd)&SQ>"
    "f0pjZ}r@EUnPri02rF?E;QA!t%qi9Q_cqNym?b&!oj1ZmsorMFc#hzdRRM$C3R_TsPCRmA&5na_gap5}wms8Qp=A"
    "z<C2>_Mas9%#18J4@Blzq$7%Ta>9ArqfmPdX|qUrtnk%;N)<7`nmDrO3~(ZJAbc5c*uE%g<5@!Ran}U41}LYjN+l"
    "$JqlfXbGmCjnPV_#jv6TC7-)thI#G}ydeI^&1@(?+m)MD9J_$RKEN-u}LY3O4_7xdTX^#q3Z2yvM$IV0rRx7Z8A5"
    "XCQEfOr&C3W{X+!wIKn9&Qy8J}ce#7nV*mO~q;v@FvFoi|+yd!o?Af|W{>)wn<{M#s2y^3{qEEjwQ%Q);J(lC#gV"
    "{MBqc{$I0mW67}f*sL~Rgm#>^w+dA50eij_Ql%-Mw5pMnqlT<B=tRorD=BgE{k@!_=NM`s@t@|A3u@=<MCOIE*+c"
    "Yjz?BzeKGco^wJ1EMEv+ye$-0h6kx@lwMU#kv`K>SqOFm<^xn^9L0IH^xy|VdJoM2-7QNrFcpe}<Cx$%c!)u)9~P"
    "Jljg&*l-frGW<vsU9A+Tobz+57Wkr@SXy`rFP#|z1|nBnrm|s|2lRmS=G7DBOS}>2M`{ohTnQj7$FyI)8kgTxQ>~"
    "gqsekY{1VFtZ*9>wV*4r#q0;E7DK+h>A=7$VS<!2O#FMz3d^con_~$mZ^^^PfCl<u283QE{!O+RvCKhVl<!<u!{l"
    "9NNELKzAzV~vqKeK(6L#Iu(Nm59a82zOiQ(=#e_j<>eux)4-0QX@3)&6M`(PB}P(f#sB2(LFCk6rHRWbWYl0w@%F"
    "To<fvC5qfih0aXi-6H@?hcbyaM#GKwck;I`cH{k@=6BJqdzwIB;o|WhEA#S{TaEnpOI<+zV-;Q?i(Y}LGz=Cg$<L"
    "6i$<U4(+a$5X(2TUe1Wc$Th~Mi06t=X44QksVsHG)bqL>jHp1dS?&H4!x(Fa!%d7XiqS;17^nMJE)7Lm(H6h_l!("
    "Ain2Q=0)&-nl*hFoGwBlzRbW6{tDTKJvV53RDz<(SwwHt)L2I0KbQr*ZQJc94C2_H1xwylI<ptn9^Y%n8oTWx-VL"
    "0BMR)+5GWThnx$gjisn<%22^1aD#T48LBlAOh$3stDbV2e%2S1r%18*T@8T^zg+~a+Sf)=ItQEFC6C$&o6>qT^>+"
    "Npx!<N;TxnSdLI=+p@ZV2-$f1o0`BakTrb)2GyWUikjnQ+8cX>djS4#30Q*#fm2exrQy&9hbVi7I=vPas<XUqn6o"
    "v)Xhz&f)sayeSQ_zQj_akD|Qx*49EP5p4XH_Ukr*ylKY+I&QSQQX6qftnG~#-Hi=&E#F|7rWehUnj1ImppgGx<o$"
    "?#_X0={4X7T`?Pl4d^em5Wk|oK_+QbnW&Q(pJ<cB3A^Dj7IcrZGNZEs-ThZ`w|)@(LcEJ!P(l_~m?Avx2?87()}M"
    "bMVOb>>Y^E10xQRTG_+Q<*I?!Lk{#CyPvKGAI1It^Sr9{i|$p{B&#!_?B$Lk5RNSg0Vq_WUqI!+k&6s1w}->G1Bs"
    "OQCf}|oQuA)N>}B|n{lbqrOK_C+1nxOwFh1G*7~DHG>FRXt#zo4(|AB-9JduZN;%t~=QuQ}*CA%LoLuY|l7RifWM"
    "9AV<(U9g?5omsg%o+1EHEBl;AyRHvl)um6hBQ2$%xo0p9Ery-!<N87+(x#+I0jGUq#{3Vs}bascIF<0Z!o6AxIU3"
    "QQ=a=0!yb-7AGfaRv|>rF}#%ak&njflFh5b@G3XYgch|mWu0mf;l4sa@lc{aWl<jSqJ={=(7cbvrNA8W^nI)hk^r"
    "->^&+U$gnq4AmA>vK%6R2}j!r`TwX~PBsYWPy^8n=K)QAiibVmX5medqorvg9EcMy@7{QKUbCH2ZjUhjE2$o66P?"
    "J`e9r0Y5sJD6l@&7w#VvZD`^^INSxV&v2s(p$OjzzI`Bvd65K=_38@63o)@wSaXSrp;wm`54Q1j$r5qWiVw4W7~o"
    "nBnaHmuobx)qce1)lrj~W9X%h9prKn4(STox#vyP@Oc;z1i_5d&bWuiHh9#2V$Z8D3oNy&yUW1gF4Sk=WSpj?HZ3"
    "ua&#b6(Yb(Dc&+w`8eZky&=VZf%-Qz9m*{^!wtp(On^R(-ujrD52%y+RmQheq^`aB4-9TEdIlyF&ZV>oqc+@!C)>"
    "0qqjWyZ?Z$IHGEm?3;y!yKB6{#17|hv)MVNsRy0}k7-Hk*G`ab9rCPoblOrL%AbA+|DA21Ybqi;=T+7e#2GfrH@t"
    "A-DFv)OTu!d@hK$xq((!n9)1Ri(E+?s%ING>GcFd0BL!L>XiRQuRO8HUY>L~^^U`9MEYBu8o3u|-6hp3bMLp93U+"
    "2{+z!D%{X-(JqyjLiqf2wHCQVMX^B60qus=~N^sFcz$k-6KV*I2tylBT;;8@kXPDq!%$WKS>%`7Wdg!D|wnceoQr"
    "T3uyYR*>n(q2(;O83A$`XrWEIgb@Y$0NM#|CHBe3XFhoqOj-p~tp__!N&9p<sB>=%){0uTRypN;%NDK6E0_}4dO6"
    "o;O@hYh>nA#$!M35vRo~$kRc5_S9+jTgpDd(OqC(<;x+1e^A##<KaY8azi<bGr4_3PuKzxVbwDuWivIHp(U_&&$l"
    "w9e(~UT(YFuK#oMMOdy)8d%1oi0(6)XrZx^+G=bzGtg^EbK;meN^7tE{Rj<zVfD43^8AbX``|40DxF@g&ZDVo6|r"
    "p^RO$dYlvS%Mu2%^2#;$v^(8L7b9X>A}rJO5)s-fLf%^Go;*Nsw)4v@J<;qclhUJL^H3d@_aEQaaBSLw$rQR+vj!"
    "qiAIS)}=g<mL(sicr~9_-iQZLpbMccSMT1p^zGWPGfH78CKb_HD2+n8@cU&m7FhgkUjHUlk<zH@Z>XbVfD_}-Igx"
    "*0pUy~9hGhG>)VxmeIceDFeD>J;X}T~dV@AvQmw)05#6A6L8<+m2djyBpND#=jqtX1Dx9Qo)1grtJlmoD_+8U0gp"
    "35YZ(9YfmU6X;AQNd0=v`01Wk!0OQE4;NlMq#)S&rdoxH<~E#iJlC;x=-!d{E!v@ho4oVZa5KIQ}@pLN<f+IvTd?"
    "PdAKf^6w^pNw!udMo$SH-3VNQo*Am>K76Pkty<B-11!y4oI_<!=oggy0TVANJgC0#6DA}@+l5yfuRg~Tpp9F*GWT"
    "eTwK4D&$`jNyu&irjsg5UeiDXf_a8@6NKE?nL56yHZ3?Oluiy}CF?3Uc*u9}4?6tR&8$L~+xD6wv(WdoV5iXjVol"
    "7esj=zhxUff|0ISz1QF(xSsuflLfYl5IX~p^EE$Lvq|*M-J|Qz3cq_WP7E=S$ah79iIJJ3FLC#+=T65BJ0K}Jibr"
    "fc-b_{42V$&Tk)Vs2%+g=TR=FD#9R-VWl+<{)*G~0*B(hgsfW0qm&RF&suArX28C|y;*%H28cCi$2u;C@vZT(>He"
    ";>7j5sF?=Pk#!#C9p5=#!~0Y<S@$cooa@d`_FBs-S9dNy9*IPOx8GZ_ieKqPXhXO{PQ?uTgHHA|>AmgO;+u(#nAA"
    "jId<??ok*Y-Hfg1^v&^M-@Kv;y`=E2u`Cm(Qx@|RQ-W^LMM7~^CKf1g(rG}J3zSIhh`=pX3LdsgOB4}Xqa~2&-J?"
    "4fT0HG2ymo%w**}HX`@P>zd&h@62afPw_!OC2_(N)hxyP6IRr@9L#Qxqvud=D0RR6{%NRjGx%W1k;NUuc_gH7KMa"
    "z<Z)1h_cQFqLLHOt4*gI^G=4N2uw%UV`}ld6n(xmBDO0mL4$e^n9T2?P7gMY71MpdL3r5k=NPYr{7$85s397{nFL"
    "!Mnf~ZX?BC&pk%oi^hrm0H+{A9TmR$~=xqO|-%mku=$Z__T~jHfYZm_Yt?vn=;F(`Bjd(8`j6|S+H+`MnVzo){MS"
    "2I*ZCa$Ly{}bD&l|d9(ql6Yx#i!+NoVWfA%PB^cD25@V=(iWeNJwFXy*&_<+LxQ{Xz|$8!dr8KKASJ8S6Vm(e>>a"
    "C=Y73&*;a3;O457;A`Fk_chLp!?~x6jz!H_T=XRUqc2srb4{H3rWJLtl_l%CL*TVlUNuR*#Y64As@2>zUAN$5Bbz"
    "9DB)nA2dOhzvAF2U(Ndjaf-H^ib8Kx}-ddpiub?#$g|J$tNWAl(A7B(5qFruEgh=5xq^q|pfwnzC4YlmZ@=*XM8z"
    "F6Z8yWncqnK78b=Z97GJ4(^t)G+EKhDe22|Js|Wmkm&g_=MagBtW7ChJDHukcb5XH#cUews4|~ltnrttimuXX!*O"
    "{yl0rpFWD`hGjF({ybP;JoI>ZvT?k_jAp@s&Z~p|_@a|dL*fL`XDUjR9lPpp>**A=SHkV~|;Q{$CGFGj593Gwa_u"
    "ll(G_J9@&J4Z29ISw-kT+DZ6O`$T&;Gq>&Ny(YTJbXt9Z5s%C>4IF<8ly$zDU9*b-$Z0`X91etxPWR%WR%^8+gP?"
    "@WPUIcIB9DFJpV@_5pjYrlGdB7fpoX0W%=T+s}ZZC+D||%qEP|7Vu8-mOZf&Nkd3Smx^(erdav-V}L;XIc#)Tzem"
    "s-?l@mfbdC}EVEk>y6Xg+WypY7YH(5^%Jz`Qx?Q3zHk8EE{LF<vyfNUqxbI@9yO<i>a`Y-p7dtB{GfvA<Wc6OaJ%"
    "EAj$F%kzkG}7FSbm?4Y_v-CgoarJc^7xhz^9^9gh-;#>S|%()5*6TPvt);3?AN-UVw|{y8(VmmB&Dum*Vek_BSXo"
    "f=9KB8OFBMTLb`&ZS6C?TVNVUtV0hf_cd#DpJb6*lra>y=a~1?l!x2IqeE)B6dQ{UIL`;-{wT~<HWW=JTZl&ziNA"
    "$S&`e5gG4me{Kq5JL;W~Jt1bihfpj7eCCH)HkBr^q`E!NCH4tg+@*;&fe+x&$NWa66F_u-_XmclIe#g6C2|kvKY7"
    "z_;Y+t-#^Wm^4pV<l6o~f{*;)Pm=9c37HXT3iV(U0aJJx?bx2e6CaBLVYWB`M#r@gFjW8xWXN)0m18b%6ymKSn%#"
    "v5)y8U}&B>eH-Cl1G<ADkSv&=8<>bU0|Dg=rUHMXkv!wLz$BwkwhFtQhB^>#a&<+e6z_K|ybw$rOj`cluc%TbO51"
    "<4VGvtp6vK|=L5Y2mc1^e~y`U~6x(c}^Ykc4UwdHXY9=81wh~b^%&Ra<QCp{}+nRL8_K(OUp%Sd$@8(DIW11mPt3"
    "?P119W<dKF$<6%45rDY`8D|S4?;Id?SjcFSx4s~v-C`pl^84L>}f_gT?CeRs>R6JOZZ>~mztH;jrOs6=S1?>wL)T"
    "7pEBt2bb3v8T>I_m&F!fP7C^ydVH)0>$z<ilR<+-{J1uhFdB!f2E9ax_TC9eisW`#l@*VXqV}?u{$Hpt$)3h&3sO"
    "aOCaej63jQrQ8&4*L?ub$E-ik$V%J4o&j$<BeY>yo5$P9{zbwyQ-{eQ&9A75HaE=TzSp?+WIO^Party>`&(K*uW&"
    "@Yis5k@IQs)<g+&Sm3tr@8M%AmZ_BX~`EwZWYsRNLCYFEgpoSVgAPi!NhB#+^fk6{wS(IpmnopG!RBZy4Bot(-v<"
    "e@R{NjgAgMs79OFpOKFi5sLza3+9Y7|BdmWj5)QHx4$2mN*Q0Q{rv{g}odBLgF*H5Irb3J=rb6aaar>Zw`3II0Mk"
    "k(m7_{V~bY;d^V*P-WgRlga_c5EvbX?zk{6`>t$u*;g@fzf(LY9?clVLeGy;kwN=6G^K3GfobmaUdW0p!ti{BPq7"
    "9eVI15}VA*ACmU=<X;)c0GrEC<*M$+bHx28V`b6c7-k4QUG4$4_AEM0~92Sg899gksy4GV?J(;H7VmcU+KUTX&%J"
    "-s!YrDF{f)q3`m;()um!T7am$_v=usY2O0Y26S)OGNH-%mqW7H{AFgQj>Zp5!_49D``Em~{ODLSD486^^BF6Lx%l"
    "31>7)zrpSD*Ek2|Xj-|=pl7w??CLPE_RX>X%wdq$=|-I|-Rd$e=VJK60uPTstd;BN`zYb9IFWak79&mtZ3p3n^7="
    "6sYHeZ05<TASG{jz(a6npun-bUrNX@9>UStMnWNZglYxG6U%SwzGSB@OyH@6n~Tpao4fhdX#sP{0iF>8}{;%I=u<"
    "XZC;O;`6jM*lUFaY1&S)O<>eKzL*#HkhGiOO1RK+vI6tFj&M=@d!+7QiWu|_l|ED^RXUqgfAUpyMT*61By%ZuElN"
    "%V39N{dvTx(Q6@Wdq+s^vgPXM7&P7<mK;Gu04T<V*7OMq;Unp?Y8d`g4ns*CaGyeca7W_ND?5FldyCwVKqa@+&~$"
    "0x<rnog8OKJTU-$n!G+vzIytt0XJ`t#$MAzHgZgTO&kOuNr}Y)nGO|D&~?ariemt~pMD4QJv=!*ezSYJe{|SExqu"
    "iqI(>)i73KifY)IhJZ&J};g6e3Yu%;Z9;e2$l!28J1^F?;eyulm9F3J@UI2s-6dSD@8-UmEPm^YIq*JF&sJrfPW;"
    "Mtk%l{8_tB8tYWJDV<}wq30E&YRCV8=tU*8XqVmHTpNIq<R|gy8i8kEY}b#t5`)DL;m&X_+T%22`988BIKNUwgT="
    "00JABbEDrcL31`WCba}Nvzsd^*`zw)ulQSX9SOiQ+?pcd$&U)vpot#{!^Em>Lrj5u+3It=6b1o7DT1F?<48;(oOa"
    "xH?GQ>w}W;W*Q9oi~k{QS}G_fpxK$AO=G&a&|ZE}NS^u{^D^Cz6uOd6rEn<QnBg(Vej^Xzt7ji19GJ70jjAP~!kx"
    "lXHp}Nq(nHit~*091`R$hGCd84=76PIGvK}NkS;L5n}l8Vi&U|R+eO9iY;9u2&lM~a68+T$m0YfVNt_S1|f7>#mp"
    "<DEbQL(VaX-MmUqQM9Tq*q(x`ey{L60nuJH50<tnyjIa+9Hxp?>JaOMa+xMI}$KH>b^p0Pli{Fw8hv5r<mF*WfVI"
    "mDMtLm0J^$B*Y&$@1MJr^Z9ae&x<1G;sh%fM;iELNY@+r&Zih=hFJ%yl|G#{bU!AH1u?G!AtqI@&3-C9&%5A!cE^"
    "#0E2(beOcAK;#`CG%$|Aam7aj`xfFCb6JB|}oC6ohGnN-nI>WLZAd=DDh=5=y=_#IRGSm3kVN68Rg!-sV2e%0jp+"
    "!46LlLpvZZ~l|x6TZuxxOBaZ>>y#>`td7h91sROE!Oie+aYl(I3>nHz&P5OWVm`ks0uW`DsT6LWP~CPiC3yA0#ZH"
    ";Q`pjX5$|~P9JkSU<~kV8iNTCKhB6#>~$c~G89+<CI+9yC?lnuCZ3}`1cLxCsiSp-@`=dSP2O58DL9r@nf0nOIx%"
    "(itdAxpltZXU9+%Ivg7g7INwk7`>ueh!U{yG&;FV|ph!nVU!Vuqwt7Cx%=gfbNrg{^51d?2GnV}Jqh)NR!JK?YQo"
    "+FrFaGRVXCnPO6k5cgf01mw>gfFW~(n;RFFWj|y6F%UpQ7-LRhgHa^_Ba<zx-qWdthff_h<(EyqFGq!;Vd}sWO<X"
    "<lk^h%dM%<1<$68?GC6^bFy*hEn$eco(%m4|&v`I{A)PRzU@dfaHPV*QhN3Q7H22fD-wFf^#cJ<STulL_wQ4VTY#"
    "|??_<I}jIb<tn3gu4Sv1F8>7;g5*wf2bHq}E6}|9@afr}tQU*1c+ooyk{dy0r&Lq?S}PCP6M3eL5r{jl{$79sg;g"
    "M++1_IS}q75uj7w>uc!%*)i*Eaog=Bngu#C;X8jTWEFqvnwK76M?T4?S{CA;^sl>O!%PH#5H`yOXl2y&(<OZ2{Rf"
    "yV5>3mG0#<G&TZ4X<&`ytTMx?KLl(UX(SWPXZ;RwOU73BglS(`)_h~v9Q&*6XV{{rExp&z0IQT@Rl9oUmk)U8<M$"
    "~!B_Afy_%Uym?q(|j!^<&_(JK3m`e@|Fhl-DuB%gjU{BgyD?67oM$v^FRJSAg<JsP)N?@OwzZiH8~k1LeeW_ldqC"
    "}?x6xZ%VO_;p(L2H@urh3Ze}`dV+kU$kR7|{*vms3@9K!sf0w<IbcppO2X)&Km2CBa<)|;Xfq1Hm_fef^OD~f(E^"
    "HTu4tfidkZd*CgKr-&w7e-T`s^*@O=u-<Hj6!qWEXUf#hPsO=tlW*@<<4JU!w4+sZ_4`P?@Uv$=imzn6lN#n^u<("
    "3C3~n=lzq@<KJEKEzTT=gx9pGbn4jcS~_HbZgxTi)jV1Snob45g8|5W@s;t?``-KHW3D!7dk07|I@H?9Pct}f6U_"
    "Jlpx`;fGP-QE`-(Fbn1rA^b&-w7$?a@OBbYKC>gPvW<9vyRD<Y?TB&Yq|zxH;2!L$~3DdvFDx*I_(I!!Sk-hr#aZ"
    "QNK%&wETQ#T!ZC2SXmLoxG9WHYh@401c8g0S|`RB)bPkC%rxE!I&o64aWuyklM~lxHJGvsjhwp?Z*la(rr!fL(0R"
    "M5R2*Te1_3xSf`1-r&sLg0QESVQn3i~qlBvP1^OQqghU|}NY<1G&y>359>gs7$th&p(QUaa=t%`-4bJi#511RD^s"
    "9Fpc57riFt`VcK;+bzsi;i(p?I>siz%Bnc}^?i?~sv9Xa7h$$xjEpt*z~3lUx8EVzAYM?X=YO=id#cyAoM3LPyaj"
    "t`$PDVeNh&!zKFtyABAyc<C+#WNF~icvOg5$``}&=zNnX1WFKq{F_)uQp9VbeD}@%OXru@=^TA%a)JK^-)m2@MT)"
    "Tr=GOH%U0^7xxsc!H)e#vd*u$7yYV_1~y10Uo^)43uEsM0!XZn4(O!>$CvKR}5uZi$D&MuZY=w0z=DN)=!d&Cr@l"
    "^oB;Wf2^+`DHpC{gXX-`kr&G<TWiiW4?tsqx*Zk<CBsXsL<-iQI2gO`3)e>cwUf3+nZi&1G+6i2v!I+h8V0f0%lT"
    "@k{vy`#r<x_#`8~f<fYf?-~%k>aJG1fJuwQkm^Dk5OXtYc-3-D0d^TG&@Z99r=^*PE)NCK>HChj1O~;e2sCcw_v5"
    "n(knP{@_HaxHV3`0^H{nD{*oWV84^z~;Sfb0XBD@*|D7c=T_|4l2|{#MOPx5E@Y%DNNm_6fHKbPsvXChX{o^qs;m"
    "f9l2n#tJtItDuJ{8YMe)YIucCLJ&R%q$-gh#ST(DJ;!ZXq)re-yiXfPzig21Xx2~4<HljHw|A0!)878}$;MrLe4a"
    "c|yl@@fuy(;b@T>ik6HGq{2gNZDvjrE9l4id_MI!s)>FfgtIh|zXgRk{mcC3W~`@W<|2K3OPWN*%Ed$a%*+KcHOq"
    "}Qlr>f?CW&kLo1;ThY7Brum~B(3YtNj}jl3NldW=Y{^H?$|@D95n>=nrCTVNJz0?c|xCgp6K%(`B3owovV;$<9c6"
    "l*0J93c^O3BJrb*8!kRbx>Re0WVxBq{Sr;Mzt}LCvyPdGn8N8#GDXb?dkA(&?8U%~uO|t3{_?hVIRId-oNk7lV(N"
    "v*eEc3#qd11xC<TbB5C_Nk<Fb65(eD=o*Sn)&N09=-zcRgu*+Gr&kY<r@2n|Dpl#p0ckOe}W`9hw2O2v1(;d!P`6"
    "0e7Ex^gFlOxFto@Jl9f?PB<u*gu`4Cb&<_3E=W$oQe&gRa=e_hlLHLIw(J>=7&8)1({bBRK4Ipv<#~C`Tq55-ge7"
    ";BRBKQ;QcMaz#;90i>1T%XZ>A2(KC>SWj)y-yyeS_D$DyE!9KD)ZqDB9Q8EzywIYBeIM%OQiihd~DwkK7L>M&u;C"
    "_z91TyRCAHjNRm^Jd5~_TiyXIv)KKWoH<K*!EpGwJm3A6i-SmCO&h5WplgW62H`m8((YF51`4IZR)cCvy4ylOdAx"
    "bckdSR0}Hn~KNZ<37bn_lf12HVq1CB=+@+;SJqEexHn%Wx)MB(416Q;chFLzMYyo?TRYv!UwzDx8RJ)pb{x}4me7"
    "tRR=m=auR+)Y&fbb5FK4N~SvjEwNk+)FVN)2NsN1p>lxDbV4e5iadyB4LxlUm1Fv+zX^YII7Fz|jZce-?5KQ14O%"
    "m_Qc35G<{sRUpF`ob|!nVjy)d;9gHncg(_&l;LPDHk`<X01R|2-MheEoZrl8stzOPT&)Ev{&F>_q$(3PuZdwvvwT"
    "WG_0f;F)|{kG_Z6Tkal>n=!<&vJAtj|iQxJHklrX=TCFycFqN1ofySu&Dr@cMS%d}=Wye|QpN>K7Eij;9AZ~EMsG"
    ")Fp1&PUS}lSt-Rk|{a)+kwq&N#J=PAd7U4-u&^<NhE<WZfRl})}a!1O1V>}2LZ?s66b=d@&^rt;db#RRbwz7QLq4"
    "xhh>;?q8LCZ=~dLH{3?@-CG6SZYWJi!<HYdRV!p&w3Jy#{Pa)QB#S9@z-+}Arv)PB|7^X<+Qz;vAH>ENX`^L$96E"
    "QH>KWo-KB?rTES@{}|v6*}7j(9I>)=0w$x^<HpY%mUbdWzkOBpkMz6g+E3zZ5b-x!O)KSs~dhNlQQly(0M_5P4Zd"
    "JvjQ+^T`ziu+aJk!Yi)=s0&5O!BVm1bW$3M7q08V&bk<zS2GYV66(S`kM0gz-GIXUyDH4CzyaNPDn8(ZRzxCG%sx"
    "|ZL_aWqKl-FzpoXIreA4GP+{ZWGH#<LqqL4W4y<>KWPxM)Sw40o#V@#DRSOV0Ic;7>TzL{3Cd-Ue;wDFkoNT!|>_"
    "~+xJH?I*c<is&h!e6oD5MBM0mi&!bGQM0~G@J;g!?jnVYjDGjoH5)eWFs<)sgw<<ed+{*f)9GvE8=O~WvQ^o+}Hj"
    "_?reXN%vs5sM^jKp*J6VR4yg-(AX&kqgYj8PLEapd{$*U2G4zKn(fk&tLe;Y7OR5je*|uvfkKbI$JKC7w8I@9Prl"
    "2e8b3uhlc`d!Z2G$Dl%q$|@^Rz0(QP5vU7q?$XBIPazxv)t7lu>uqk@o2{(O?vJ!NW$8K^iL<*IM#v<MqzT$p%MT"
    "(LG716x$~{J~xnk@J&vDETRd;i;c&PV2tR*nmqKjr#GX`{tJQmtK@K&Y;KxFS9Z+86%aPj#+=RD$&O7~=Hw+5lt7"
    "R&8B83>)6o&r1WWmH0{McnRuRp}x`A#=(5Gh?>JL88jK9$MZJiWpQAPp?)Yx^it40w1WQTR$zw@bXMzJyjA~eqP3"
    "Z6bZkjLr1f#4@INVSe)d_woo2~MxVmMNG6c#VNKATj4H(@bsx2nqC%wE(z&mClEoAGq@h_y0Aj!P({}jF+7yRJtN"
    "f(26?_vy$O|Y{tv}!0p`J)GWPgOyuGAZHj^<=;w=MnPWA8UnOS@la)x;#tCE6KPTAF=Go;O9Z#(!A7|OM3CcOo7B"
    "}eG$1lSI&@e__nt)lcT0%9x=1X=^H+C2E@#b#wb#k)*^Zwx}mVNq=n>;$ukaFz50`nfEOHADw0K~8XG9lwQyP%-t"
    "!5o7hDWWRH-Zg{lJjECYI4W18A#AgDRLCYXJzyPP6}!7H(16>LA4nDe!E-(@2sYJ!S~i=K9~IjmofS;TN-<I*IXX"
    "#DtQ-L%CVRLKQ&3sV;e&~9-e!x<^W|tP%RH0E&yogvkzt6<F??aHU-+6;*{_#Vxqy%zVXGNbv9n>*&Wt{Ec8w)!V"
    "Z1j}(2jnPOhr@S7LGJoVzSK}EGIF^FmZ5{Pg;pHrtaq$L>r8lk#sfki)oEqm@4c|o@qtW*&zR#IZ^)g)2*k^Hn+a"
    "teEP#CMi~FFNpsp9<(oQ>O&n#@o~-r+7P7gi$z`Kl^*7Z4U9T-cyrp?+oG{5#lu{sErdLczRKFLI9P7s6O<MRRCt"
    "%)RHxxqQJB=IgKB{notm}|K`04sa2^jYvCA^`XB*zq5bT{+LFsI%-`DT51%j`GT9=B=BLq$)60)jtwHD|5J&W{#0"
    "gHcm!xCsZ`X#hUZc3mRHn&MT)iDuhUE!j~DvS50I8_r`Px+Hi$u-0s`)B;5$Q7-RLYB@6yaxwfPtutr@%n>OU)rp"
    "6{b4)*6j`gQ=R3kA+xKhI%`mUh@y<b2A+q8>)0<*?w;PpO2pDsHi6=D|fT_^g0QKCPi_>J`uk%s9812HNFb8;9cI"
    "$K$q!PnXM+F7ZJf5PY540IN}_yW<WyHM?Zk`TwuXE$AWj!ctxj>S=Kc;TaW?ALPMu->g^^a~9hMZ~(M^FCjSz8}g"
    "T1iMZ`v6uoCDfHL8(~^HJ?=}GqZZbSDLNh}TM(XxohzJy>!1z6gz%i?mGp2Rs7>uzxIf|+{Ebws5AIC%Xn%Bg$M>"
    ")<X1AAOSq$By^bmC0qa{>%;!O@V8FYoeMhd)gmExQ4^LD_}(9^S^p7!WG}`7tb2O91U0?Ek$-JR4KlY1nbLNo91-"
    "62GYM$?48P4@SP7F|BV<fhCR|%mM6UJf1Bn51KBnnk`s)|EJ#0=?PjIF$hs>bWkX%y9^PGwwMrsL_+i85(xmX83j"
    "<@U`+0Cc1dB3%iPI+CQ^g7wt$j?gti#pmeG;$^xOLKLIKQ$z808d72hJt`cz?b;rc<iytw08)>3ETr<H1?+M-qKv"
    "39-D^lrfd!K1X%7u;w@T)ehlYFn{_dN&a4wQK6OMJP@N55Xa`oGs@bqvZ?Xu_j1sGAJBx8Mad7H#{-F&k<d+q>Q<"
    "#>F^_}B}2<)b6b<ahQVN93`gL!*JMNbf&LIAT$iQjjdxSuR$%WGQKuXrIQn{~pw&|kXPl2F%Q4Z;X#|HC@X2h!fm"
    "-xFV2i{P@dIculiOyXM-lJ-5gzw5`Z$dP@&dhT-XaObk%n3Gfomw7L?agjVbR+peAo<D?VZOr?18l^FjoM@yO9N`"
    "t<XMP8cR_OJ0RJrPkT3S(4LvC+?ii4amBCcrgkRavM$}S#~SGn59at<+H$*ZweemmkHf?_HxU+GoRs)Z_uV6mdrs"
    "(mSeP3D%2d_$r|_gJrs9HXb_oLpfg4_A@GxT?7~8A7dvt)Vumt^gYM<4j7c9vl=U2PICaRdyJH!v$=025q_bspge"
    "apAj(JYHVkw7#A1edjh`8e0)&n}R%|BYE^m(4u+<OJ(lLY6Pj`5P27XTN5zH(=EWby2RUz@volX)QFP&Ml~5s(qJ"
    "+x(*@z?vVyUwu;NwjpZP7H%^FLj}&}1{Wt<%%bAECxOm)lo?-JeLYKUO{+)3)?@D~BnJ&h`)S4_lSUpvelq}C~FJ"
    "_am$?+f0u$B=U(SqsX$R(4-TV|?hHDDj5E1@Y4Y97h@BG`Nm!{P}c(8c$jpR2$CY6UsUIg8kg>dzAI$0q5$UIGpq"
    "U1We_-5+IOktZqv1D`_NDtKwshRCo{2S^+``s@n$h&o`0D}o4Q;|d7L03kIXuZ)>^$wQl)5+CG~QZzNnY&N{=m6C"
    "0O%5!`5*!(mOJ%#Hz4E)&r&fA(<Wbapfhr*Zq6(ENjjIPu1=G79Qzk04FpTr&I<d-*_r@fuR+i`4k!odtWVt7miF"
    "5>M<MATR(H+F;KDTWwRaf1Huru|a5ENk+vd<<5P;Z6S9cUZP#S}R{Zzh%7+ZMIZrO;zm`!(*J3KRU;?xKZ!X7Yzx"
    "sZ%$Gm2=mPWNa%UyzaHNfyk+(SqdCjBgPIFe?FKEF&4p8J98cg#z3_b)BU}et9;%**u2f+Zt~L6;#9`He6}}$_72"
    "Gk9GKyUpu=s&Wcx8WZl{pu40cR8GX3})OR0DVA!T8+yro+dHwe^jtSBIn1E0rtCugFI)RI4SGifx%hhh+pj-JMP;"
    "cc+J(HJ}@(d<W=$<#drXBIzLP0#dF<9&r)bh;1Ax+yV8X2TzsF9qu{DO#IvBCv8m8{1tPTP>0ks3UCmZ`!W*~7N2"
    "#T2g{QySg@4K?m7eev*iaWcrZT@0#Kdww&hUtF=WEJ!m0_@A{u3kuXG4@)NU?jJPr$XHb}syNN$*2Fmf41aY7^vd"
    "a!4|)}iD_s}Tigx^LX4m#{J>&C@%GJYEfA6MrxYbN*bB(8>^T$nZ@^n5QJYIw0XkSBMQXnj<tI$DW(g_O}64`1u-"
    "8i9fg&Cdv?H5<T9u$|KrV%Bcw6UWpp&qQ)X5SnVDOQ$EN*BpuBhB%aI)5;WO~aQwm5Y&6Jnlvu@J^uFRfwgUOUa1"
    "2TQaQ3=4WQnc{w=9FUe#|;p<K&~(Ff`yl1j9nCr!C$U#vN$90kT08bKr@Id8EBygX#!L?hAU^o|6%NLtJVb$y?*j"
    "POfHDv9}c&#`9#qM|<7|d12svvY?iDt<^VN9FTn0trCYd?A4=U{g7t3F#%>cyTKkzZzqh!hCOXqAHuuuqjW4#BZv"
    "<1;x<|o1%Td`*@ZeY-P#|)#7kr>^MJuZ>w>6*gw_r5**Lh;b(J*KbtUdN@%7-9;&v+rVgcI}2TITfl}u(_no%mxV"
    "r&yNUcMqXS2nD|1GCtOzGY<R_^w+S$a9Zb&zQJ84E-wmmWOhVd(4ABRzc|6N-Ru-m~#EFwN*qx?Vfs`VF(YKvr?T"
    "M)dR{giiKTn4GO8zB{xHys{#@^VSG9|7>^wA++5Aj!j7*aRd1NGo&cV6xHf4<02D`UbKk1&<XW$T)%4`&Ve~yCG1"
    "R0SL1^wrt=1*$DI#W!Lrg$GXbip3q78e%H=akv++eb`Q4)AzsOeRjR~-z3*MrhVPiS6?X7VnZ`ZVN=ZP>MO_YL&A"
    "%}{=Q6kAA%*<r~}4DI}EoOX3E%09jpTJcJ8_OOLxDV*y@t56-VKY*THWWXr!%3?O-kTjU$1hYWKKtM?o@m6XlRI*"
    "(AK(oSOZQIwwK{g&c>R6M_jq)hJ8x~G2@dNp8MZRf0QlQmN8-P+DJEn*Umkss0=LYUY<4?oP1J9+^raurza~id(l"
    "n(mStOHS?QuNhHDGn)k5^HV8t~oAA6Nx$Hgkr8w)21GRa^~(zyoppc<|5JJHtZws_YqY6zVT{uht`u@0Q;l|N1#E"
    "VY*y90VNCMs-W+pyDe+>tk0jwbby{p`be+_ZXBwYSCpMDOx%caRE8|G|+Jm(m`qwnJKUu;S&PV?wJ5|tzez63p78"
    "HeDhUY$P5Hi4ayNw;~5xeVkB(kroJ2v|Vb$ihwjAOSgz0?bIu1E(9?kWV+Bp<CkdK~rBm+XnKt|VM_TVva=wY)C{"
    "CzC2Aj=5gpXi7z&2tm0i@iJ#?CtGESsPIpuXzw1~kxPHJFdwLFM@-+*g4<kJ3rV89i?KhOROPtP(7jHxS%9=uzP("
    "q&(y%MetDWB(FeEp_!KRFq3}jD`Zh}^|w9v0;RB4_mHeGZI6TjVhAI-K~vv+-Dt`WV^nG=GLvBn^b-#WK$kNQ<(n"
    "l9;X2iNkJhgh}T7Sm@+*GEW|Hi{3Af+}800DyCuzk`PGAhIpcgbb4EkWMaa=hNUGH{-JR=tSX(?Rd3TYqw%5!e~8"
    "g3ktkDfQ+GBv8F2UJu+|9p77#|x*_#x;tbYXNr7Yv*tZPHw?=3$?Xm?pBPV-s5R-%bSNo^HVr#C-sq8&i&hy#a&a"
    "azLfo)nW_NKC5qPAO9{#0+uJ5*nr>jfi(DA=vB)p7$<v+?M1WcqRBZ(aOJI@rgx;a+M{0attyb97yVYQ8t_7m5x>"
    "vBQCVaMVY|!mFc}rZ#3%5ckmz)6m%!D<yGiA}>DqQGmt$YdC3<oQdy+CB%t;QT4!oQ2O)5T8<%{FUo5`3ZE0<jan"
    "mNPZ(2`o&}Ef@$4onI<HHXg}$W^b>91}o4qk3i?qBizR;i)&^ge=4`KQEnlLL=6>?^#)rH{irVk8QG>Iq<7C5p-!"
    "=@2?*zC>9yC!6Y@!JKXI~{Kim)AoHps-}LA;+X;-oru;PGv4B4J7YYZo3@Eq-(}{ySe?oO|-wf3;n~irgphzgn(5"
    "vpm#Z4j40lVe@c&Y6kr<^`h^n#f)o8*OQBnXtrmNp>%rQGMPH)Ff<(2_2IvvswB0$y?t65$PM>rKDS}St@&Jn5Zr"
    "yeCx%B1JF`1w!89#27@cB547Y@%#f^+UzLHPff{=X5^H@v!()r55Pi_ua`LY;Fbe3liJ5>dpMQmHt6VLstE-gaDE"
    "elJ{^vS@0(zUkq-zW;&!q%OKQRH6!aTZ!P*qJ!Ej@@iu2p5n#_!E0Pn0ep`rA<n><1TE|@#Xo8F^u=*js@2}<3o8"
    "Bu^ymZmV3{SmU~o=u91DE)g%M6_^5d8-82Pq4PABKXl#-r0AemC`6b?+X2xmf(EudL#AL3+PI=ils=+$z(7;T~_P"
    "fwj1Beh2%%1N8*)4`V4n6jK;*>zCC*EbE-F!Jal8M%P$efkXy4gMeIfmM|wt)~xX#{|v?>p#6lZDhx;<k*u|T7ym"
    ")@Vn@+?L-w*IqBHX$Gb9`4$}EllAn$Bh&{kLh!PzGHkS{wJ-3g;McJVH9pZto5Id4@zJ={rj5U`?8R4@n;e-xll}"
    "Vv?HN|NBxfMguZeljIp?OKpxPg_YOqi?Jcf=Lqc%_(rJso5@NowRq?^_W1(pWR%hB-RKCbKUO_IFQVgl4jLlt>%b"
    "liq1zJQiHX%V9QbhxdvW64?s%>gN@P5M%g2H0lcit!w)5w%#{*R3U+|k{Bka*&~AF40zIE1B?h!MxR^{PwH3$iSl"
    ")m`u%DO`$>|Gk4VLCW4e!ZT8z<@L@Yt5D9qbPbL{@(W57>}I0UTwF9u`*tHSCTz|=rpps&!&)Zp<P%bHSW2@W6e{"
    "1;gKm5T`0htp#QjG`Gwqm<b|eW9%ej6&NjPtd<eCS$(wme<QI$1s;ne-&OR0k$0{3hy5k+|JZXAb){jpdT|nrc{b"
    "ydP#KyKj}9%WO8nys({!7*tV$*v22WD3mKkJHnQ_|-YUpM&g&>m&=3fOICSd)u^eGnz|i7sIS^eCJn3qB-aTyIK3"
    "c9YcN-$?e0~+95S@JmyRcsg*@k?xYj}m3L~%rCTK4(MxpvoJL8~FLnm0L8uFD7NkL~cc3yc-Gs$y__wmROYT2kGq"
    "mQYiaURJTHby&{7fSPi}(RFC*zlaa=#Ma@4aayDluRwcT=2^H|M##Kb72c|(r}lOC#+Rdr)dSX(305;HwkD1<BD4"
    "c+Oh@`o$^`@*F~KN}9$1>6PnXT-??;^Zu=`fk;y`u%l!fEuV@#`v0d@v;e3(`>qjCtUWcRU+6zI}X8fP9dikh^Aq"
    "Q9j{8W(eLwZOos|L`i6nU`7!BKzmey``3fK1C|F60MZst)N8_jeWKTS8wEYE7>^iogV+bp)A;CxXzbDj$0hnn_1W"
    "U^<-OT+BIJ*4&bf9^4!v;Ic(WnD`KMuJ#Q=*#RMN>jJQ^lW!qrcT{lzt!X68ucV=cNzB}7ynKjl4+mb4`?nhZ}wR"
    "Jw3MoBvr6RDzxA1{VV>^1(ngk-S<&Z7lw+IVcQYv#TrX9pY(#pQr2bLRuw%K;$m4UUmn)9gkH=@>1Hiqec0wmH3U"
    "I-Vvd2uyPQu?BFkFK6>x3Ild#!9c?D-qyofW*bz4m}eI}`P;#0;TJrY5|hcVI|nVQ7Kq80AF|t=e%)Y-0Yzy}Mwf"
    "G`2XfE2F|3KZUJ%*-LK0Z@DYC*kjnd@GB%P+1;$P8BEn-vLnckL~6KxD7Ms`k8)3<H+uf110C<MOR|M__5bpPnEz"
    "x~6#2I)WD^2d3)b<c6OgK@U+InL8yoTv93=bK=hZ|*tHx4}5y-gBJqf^ojP=Qz)Tah@UiICwy9n)qnEKHm8m@I=m"
    "2AI}q3f;xQuZn}HiL*{h4^V2~u*?&p3zk0vzpPZf~{Mo)eYAPpd-!tIFy`Ou>$?N0&S3AeQC%^Q57fQg{geVdvr@"
    "h}!Y1G3v2L~V<RDV;_Y8xhCG4_#U=gsNS{vizWs&{xQp9FT`eJXi#xc|2|J-JKuy}kPyMkTGGWB06Jx8^EL8JLDY"
    "w<4e<t!2I8bM)@69NMPxMHd(QvfO%kblltj`4GoyI9)H2<K9c)z=yj%yTS$)j$ScesqFcMpuv?)zSQ7OBHPL@NV&"
    "lnNHwwgbGCwq_qG8s0k<IXv?+-0KF_eKwQ0uRUk9+GYwF!mcX6x1evO%1>G(@+tEu9=a(J({<ijlxUdl$-i!XO3O"
    "#PNdoEkjPhhUqA%Yj3&KP(?~eA}vI^#`Pdhv687eUc{k;r(Q<_j2dW!D+H(o^)HLln!@~<#<gwR^y)A)Z-ziA$4z"
    "8&j8fK<#mPvLltu^pM#an9YMtrOg1-@9g1mSsXm*6h%%szUdrsuF(VW86yr~)Iy4l^CSj7&aOf&M$MSkOpjIG<_t"
    "1uMCh9j!7H6bPo$Z0z3D=xfAZJ|bo{IKUg?a_w@&3;U_L!K`pU(Om@b+%{QxA!+>iS2A@(AAedH+xflCrXUyt9AO"
    "YwY}VbbQ)MHnfn)Jd=zH0!2q6=~Q*xKxp<3_nz0D80f^AGcj5515Atuj!cZ8-&4w}sTH(is9N4&E)eLRoRiy5c4y"
    "<|WXc}^=`8yLjwT42+}|nX(ax7}QifVR{y$G(`hsj&Xw@lFl}@pDJdlZV7>a}qr?4sv<ccm>to0Nix3jmG>>eGwd"
    "3BiVpD6APvEmUcrXB1Im7dSBssz@RgkiL_!iY+X3kdKH7fBg6Cm_rNO2a)yQJ4pRmJg)iK+Y^e8eJl9JzqVN_O=L"
    "4trEJ8jT&QU|B7;Q`J7;~H@d_;W$LYkm2I)n)@XXYTuA>d?!KO-!#3!+jD4IjOiA`rF2B2=nshWC73N*&Ndm-iYV"
    "YJTwhmLuH|)S9OY<d~h-V+AEf}RwbDLT&^<D$+^mu>B>!^U3oV@+Rz20vn0!3f&kIxmIHonntds*oAl#$49d=hyE"
    "n7jm)>m#PYjxH}j{h~6XY4W;vyt#XHcnGH#-h-o+UQSZRKPnJ=oy`}wx;3oN@p-^<Z$4$XT&8nMJfCxlHz&g`W^n"
    "X@V2bti=opal^})_=?<|?|5w!+B-fvR<2GWR~+Z)U%ZyvY*7X4pKY8;#<Tqw%)pX1HH%En{t4KSLbm69LSR&y7#@"
    "pyKF*LJVcYs8;zYVkmQ?HFya7&D*(_tV7zQ$;zX`!LW)PF_d*BpVx-Q;zT+5?};409=L#cifxK1hgF_V0`SUWrKj"
    "_=4zG`QAo$s_>t>HV+!kxC*kn8tJ!!cJtB4vf0wRz?WE_hK6L+0uy(YRF3{e7H7Wl*1IP|6>DRrpr2p5y_73&Eh7"
    "kX4uQ8V6R6Feb%I$&f%P?d<F^*wy-^KoK0|5aW;$DnL*v2DALa&sDwskza)X)OB1!rw?JzG#GT@YG2$>L@vU21Y9"
    "Hq2Cz(Np?2p9*+S${J)NVn3Xy$|=(HFtrCDnGjC|wg{odh%lBBOs-N2usE0Md4T45dW)!v5w&<$1v9jY1QxHY)KD"
    "%iFbtMVH4Tk|y)Bc|zJPfnzBk|bdqZw-b4YV47l`ZROT@3w$FuVmSBxTSr;2RSbOB+F*B1g%d_2J#xlG`2uuXiBT"
    "VyA5Dj<!!ip36aS80QY>I0(MEdw&q7WAP=@Oicg_crrvp<Og_@0m|vrGNoRBXm_b58?$jwh0)B(ThU{QpP!8S|Pi"
    "Qjlm{$s%uFj)qcfskIQ?q0Q1U8@6=Y)!}tS}Sc*pQKD7WJETohM9OVDSt<g4`EuOua7u+d!ld^Z6r-C=V0LALp?V"
    "}sz$oMQI6m#IV<n%}vOzVksi^NFy#Ey>X?0g1i5qFry6RgMNb-)tVrVUep$x#C@{s5JCPJxy&yQBg#@D!Dq(jaDR"
    "FT^jkR~Q0##LqD<t+e#vCqSRAG(u@Xx__O8YF*P}Ozsl!_0LVyxP){By6S#`Wz}OfyO4H*^$|p9Mb9J`EC3?Q)xF"
    "O_ke^9^Tai<dx}!dVLTN}Bj77&ephe@+^VKg&70wDdG=3WX?4Jggfq+mo1i17NB~h7~QuZ8X$5B&Vtn5W{23E3{x"
    ">wk#hd7Ric}^ea78+ri?c`)JUk(-|eh);KlU`a#ac4QwYdiyR#L<p2!Fo1I=EbD}Jd*W7(w}AnnG&5+PYW;QkoiN"
    "H@JiXIln8z>)+)EzdeZPF){<tW^2w-4*L~i%>sm9lJvKrV-O7ke1b^B&-Tf<yQAQbJGajq5D7#=y84<I%qO)&W!P"
    ";U%Yf;}J$p=d_!J1JIGsBV?jIs_FFt++S%Fi@n>03xqsRTB6DrDkHA~LdW6t}IkmE$=E&R&f#E*w7JeX<&<(#y+v"
    "c3Gxb8YIf|Y`BhbuO5ayG@bQ;7f@U8UO;nKE8p(hG0TTPdeQu$4D>UHjMLQbeVTd#awHO{4Q%JZ^|Y`=ARK{?vKG"
    "G?m6kDMo`K`EXrMj{9QmT}Kg<y-T-r-8UutZTY)WFrl1s%Tbas@QnkJs8iAud4l8=X+<(gs%8W<*DEGJnz*<TpbR"
    "Yr+cH$aAUZ9L!-6!9UQb8O*9itEQw%1SXFz<GuR;BHX>HysLPt!*)%3DaZ+m}-|BZsu?Wm>p?{WZR+D&NFV|#;x3"
    "OvEjK^uG#<i^nU)6+GjY%i{;ktUwga1BtA_}{_-PmXgN)8z?w5-N&r%MH{bxKptYl8yN?^W9p|zCGGrhdB(bOYWq"
    "%1A9#|>t9gv7IP@%!?Mv#1M#?oLonmEx8v;*jjVIh0RN3R3OmxwXAA#lcaUcpWsxer%LaPlq?6}ujm;`mO$_eu}z"
    "5B_0A6Bo+}2?iA@Ga`g$$)3>qJQKSTo>9sBH^ye+@qB1~le2aJl~+fL4x7KY+^+PYxtyohSEd0->Z=!ga{?Nv2tX"
    "%qe)><`@<uwnB^}qq5v1ocI)?DfFK@K1jtD?a8qBer>u^S@1;qx1Jr&ko{z9@CA20$9na<^;dGuODtb5t0)$bx>V"
    "ECi+a-aYzpiu*~Pbo&SHOhH=|Ada>3Y#o{Ip9`u)w9ReM6m6xY77J7#lq}}t%HtQF%wye>Sv5l7#;#4J^&q+n_tp"
    "+hPZQsT6_UEZIq6A_}MiF$pr+Kh^ry3hMp?Q8Y-F?+FB5l6jF8Q>A#;ey+Ts^(!%!rBrczeI7@I@2<+hDQF6xU-)"
    "^@F?`3soAa{(}Y5|y*&c`D-{u-Hel~OxKVX90IWH`YS;j$nmASF!4AOhs-{Y=PiPCDRl&JF;U6PS~5>ii-wkr;-f"
    "##Ce**J9dBX7ChYAs3vV&u%&U+YSC?I>zjpQvs%)<(y+fMPKD6npD`E{Z!U`{}S`<2jf{zo<pjD+`+LdQ>5cCCo4"
    "PC!BMVO@{c2|qM5l!B;Bt;w8DyU8V!d@_v2hlmD3!%31CM^GLk3zuU_@`_Thk;4qOQk54KbD!Ca)1Ypj!^ya9N|C"
    "H9K8XO&wMvxSLu9awWp2@&ULN1mcbg$A>8qP-Tfa4i83PV06yd$8<>V}hE;&Z2)TN7-V0%O-7Zjlj(^0WuVQfwCt"
    "^l%U;z;I7?mU%;^xq%kVWHQr%s8LsLa?3Qzii}KI<!^K4%5u04nPcl<2R^&=YvRq#{vKJ#f)EABHqyJL=wH+EvJ="
    "=h96T_x0qXp;f!ngd+?q0VA!siSlrZeeKL=6x}gVBN=;B!i6qh<tx?d+0qs0SN@0OM#hs<(|Ocb?%1mu3q@mw=#="
    "k%=5ToWPS&hnZaZ&r&845S2+fC4V3dxSX<@$P@@?!RU>zQ2Foq`3QD@ej5ltzRkcj(mB@Hh_!P~Wg1>9D$-(14R-"
    "UZ<P;Z?i_eh?{qV+-JW5moT_p?jSfQLMKicfog#W&Jb4uudW1Z~0?4ABD4&x>ISr+nrmS#oYLpN~3#XW!)VDT_cN"
    "{|-46O2>-fEJyvgm5Ec!krWHLH@GaWH{r!#?g?rE6}YMjhsC57OAo1uKP;JAoBs(ov-lPKI0`-|6RcU00RyHvg-I"
    "Aj&iC>duwYL1F0N}R|@p@*~R8LuuRf+zY>Z&$x;kP;ipCmZc@K<xCheq==z#pMJ?JATQsr`*?YxP6(8TG5O?QM=C"
    "bTkz5u#>#c6V5fur$V=O0Gb%xiJH<u$yIwarcTgslHeRU--m!0eZEDzOJ6aFTr|IlEpi`au6ddK~=|+mf34yQwNx"
    "Fb5orowLkUaaXJk2J9hsog&JT=2UAREyOuPla3UQW$XhO>Lbku$R&uix>Xi{jh#(L*b7nn{RmaiC?K&W)82s2b&1"
    "A?#+lo=xQ+F|QJd?_TF#mVHe4sYe?1z{791uq2BHxGl3Fg{5iIQ2QF2FEM}@-|xOGTvFaRK%Zz3T(8v!uIBGW*Q?"
    "*^vR*GQBif$OUTLmTF>((NY6Vkl9~GIm#Aj28Ce8$iBprfgW*lpqhvCqb5k12xV*5uV;T9{w}RjKQ{;$r*d;&ssv"
    "*XkbR{EAmd^7`O``Q;M#cT{OuKG(e*d7RXuf1UTyKYl-oa?bJ{zK^TkH+t17{ljugX+RW37Y;l{g=1MTe(a&f@`U"
    "pLi$Z;rZ2;#FV8K7t0A_W{snqR-}9q#py4iA3s6M;VINFg*zNW=nYSo=l$DNDG6rYFG#=AF(JkK{Vn#j5DOE4EAL"
    "64iU}W1arKde8F0Z5Hgj>j((G;HI2OJ!KSiO_)!Ew$SFE!N0w3(Wh$tW{Vu}7o|!OYx78*+R~gB(UKB(q1P${OdR"
    "|x4SJMkR>z9SgAWz<=*+D&?(y^IRvP(OcW&j8Ic9Pdp*cFQ`^4syuBl#d&R5ARd*~@K3y9arU-#iW?zO0XJK-Gu("
    "M}HGAYW!vBDRKQBc@)A=J`T%Jrk-@<(MasgG-c_SU<=~e<2}Xj%|(zG~2+=;>V_WM%@vBhO)@0e3}@O+#zO$Lm_9"
    "JEqE$aiXL5G$O(m=OEQzCdrD-bB?gB)N**;aEnF*{$A7YLNhTNMWT26Kq+qXoS^OlM08c^zgA2(R*Q*q8L*ON^F<"
    "y3xY;>|*h-{W(x1|a8ZJ-7m85`0m*^?J1F>P*M;L{D_sN#&WUf*|*xL(-1M-=WNE-Br&ooP~7KQ7!zcI7(&0*>Tu"
    "a+d`Ww_d(EeFOOGq?O^D&#j{T6xl77tbuh5GaMTqA-#jG61gs7L@NT}Y|2XU897zV$gt+VK(ar|`@GDvwx<$3tz;"
    "w)$A~Zsk570kq8TV&Px~i--Ff;Q2doUvzx($4Z_dB@F8emS`1AL}KR?_4=KJm8;D>ZO9sKa^*5JDz&cFNfw-<l@^"
    "Y*jB_MZpee|vuM!}+tp_dk5|!_)M;EQ}W2b|dPmV+2K`tc+Wi6|WBW6T|L9MXuYqm4~i>_T27A!kxKQ1Xt?hs-i1"
    "pUiS*GEL&3r39nw3uZLD4g^&3wr|PTC4}>6v*_NWo!_M}8C{vhiIpPG<tw0}truRXj6>GgWDrp>66%r|}TscW~=|"
    "2$SICCpSna`iw{m{gjTRDQ5$yK0+&g(u%QM#skqk~C@sLqfQc3C5`T;fI^EKABxuOd(C^QU)DcH>O1DwtpAR~gPP"
    "Q@dY4f7!a$4e8$wGFskDLCF2Sqm^Yg#~>JwwJ0!}oUjKvUvxwI8}#0{8#zY^QnxDcRk6WlQwGEaC?CXAA#eQ|-pX"
    "&M15hKTvn9GhX^bX^i-XL&oM@64YtA$d%F+}zOFnelepMYUWWqwjE7itfxqO&>Ak6|jx)f@jYE*E`dfH6|<i+emM"
    "z%z>f8eLDMnizQ`jj||-iF4f$?nbx2Xd3xFU}r`aZl3A6fH6w^uv1&%UqJ_(D<ySE8YYEu|P|lw&Y?bpFc5DE6~V"
    "jDjLJz^Yn&CLwilzFULSeh!liw(4(;TE}EzT^zi?jG>0LcWK6mwZ;g}e$Dikl>GTqJSqJ#fXL)Y6M9M|yffgpaMj"
    "20x6~Ri#N`94o%*Yu?4oQ1mtab`U(yabp>fVLDZ6iq={VQ1I%rWU9Y00@vLJwzFk>y0+*pgS0lbyBnkq`+=7?S`4"
    "kd`$b{r6MXz5or9vYkD<^X$eVE{(oaS5?>LEsmv-aiYzZJgVs1d`~uNF$~@oF}y=rjvT89Jxqa|lJ((;jGsnbFwu"
    "zIp=}W_8vX1W5<74}CmB0H4Sln{U*}kGfzVVc@hlv{#>jU|+@WI8<sF0N-Lizv=^SQXNx4w6v}VbUjod_YeF{g+E"
    "YWPYS$x-%9X>LdGn8{B+f#%{3qC9i5l@*hTNrrtv4drbdQO{nt5kO+4>!6`V5VWMR+*yAaRQ6Y+(H+Vgw`-rISm;"
    "j-XvO<5B@Wbn7zeAXwln@R59cl%DUu!OnyDwLb11y6ED-{U2wsL(1$+#)F3FhU}jSoMJ11<9*c?vX}1bE-3of5PK"
    "II^V!yQSis(fnC+ean<T*3}HbY)>ZebL)sFHJ=3q1;(D6q71iiVxL4iYK3$Ll1{{zu9+BC4^U1t!K-MB|wx(nw%{"
    "&t}M=CC_o}fQ7w7ZaRX&Ie~5?jP_#phf|5QRJn3T_)%?%wV+K^n%xvH^EvuaD2k0@F3=d1E|=_|Ul%)XCeEO%eSy"
    "HAwfQCgV+eUoOy_3=+pqKE*CyMKb+oy{wFd*Cj}*m&5j<GEdPdtsHV$%LnVM%H^%F9XQhW+*DSCw*!fOeX38*B_>"
    "eHlBq-6P;ezkkiDQEmiq>K$%=6Z@qwBl1mZ=Ta%isREAq?zKR39(e+h(^+uBxjGpU?i`KB@$L{L}pIU#?f_38iRa"
    "c9^Xl{4f-u<S63YTF20YOSyy8)+N31$P_wV%bas`0h%AuklOkCbcTXmmwFp;Gy}|y`shdFpn6eoZAr|00o;a#Ifn"
    "iHHSueV8zUl7ujgaip-cm%=t|VK+!i{fKQxt*8s$#<4w*oaVn!px0H$f{w@yzNBb*1eVi7$Z<F1zEj7_Z1)&TR<="
    "2{3Dif+<KAn8f5wiHgB(-F#U1CUjWnM6ZF2Kv6)yF#$@UQTX*~^wrlePiCRI#=W2wMrOGv7A?nd`E?s8vAj(Rina"
    "$jiOzpMIy3qY3jn%=X;ZEc;KlL;!Nm?z?YrcTt<aTdrBq`x;_@Aq<rZ2svHSW-szNVu$VBI;Y^l$jmmlTPY}Sj;Z"
    "}aH+(F@{8=PddhI#zJUGYmH37dg;|)Nx@E_(WQe&)3YID@3_6%L=3BFmMOMZOR08GRi&aGNwqcvY5=0GV<(>5_Kw"
    "3X>j`Euv3mf5$^CK@X9kkOx95W%%G_)rgsv^I8Ov_FHz3(oZTOMM;Tzp;1b9LsxpVCC#N#EL;N!d#)YTn6pDc7U2"
    "J;E0XOt@M)jbUIFp+bJxOb{5s1eU$jeS`6*7H)N>s0<_!5}E7O_s=(;N=Kry>dMRL%_dqY>rOF;^KGbpV>1MY9|O"
    "EA+HhN@NDED@@Zwf-W09TPA!M`T=`Yj$~9Lg0jJwRY{f~eNW*VdM7rJlj^pOR6X+CV<aE=NaezL+9QBwe_3}KEM>"
    "gH<bPWADnbnWV%@EcC-ho)tF!07$4M>RHQ05gd4aT7AUovf4Cou3VkZ;`)DLM)bkZT=nHn;ow&?JQYORcghG+w9t"
    "hl~TvK5ROV_RWt9bahYD?Z6k{EVV)SH%&FY(>$=5>hpReaAjfv6SEeJLyu#kQlI+@lqp=A})qhqDxm|Ggf2vcp7R"
    "&8K8$gPD{|>RQeijJz;km-oue<6mv5cLc&Q-Zh<JqJjRxqeq{d!Mv8KDkuO%1IfdK(I+v6{B%`)O?jWx~V*$sil6"
    "guwfL(a(XEoEIzPxT8uRXX8A1KSd4al+|`q68Q4UwQ<6FN<)8mBDVp6)*VuDknv_vsJa6}<C9m!e6!Y1x%{OXkI0"
    "w7_)jqIU>igc|6htC1}Mv}19p;^<~I2O8wuHR+QgH4)_A71t<pVusnWMQU1%;kLZGX*Nv?q*YD-V*0X+jL~`7DxP"
    "&^kQ@ZceBFKO;N=k_{N(JD=midjVx3~pGI8N!QAmz=Oc3BDo~>e02xA*x#(ahY&on@%r}+Tf>X2I{6<?Imiyh>5H"
    "b@QQdrV+7d8lih0tLW@E+Z+*BA633eAKd7<i3KMu<cc_N<c*yOlBDsVq1y@!sfd2RG{V3li5xndta>*u$kGaD0oa"
    "fd^ZJ;Yp}(W(uTT|F@vpk#EjOTCPQ&h+W;E)3lKz@^MY#`wa&?&kS0h>G^X&aNjl+B_pJ?O!mfF|y~mM=C!9aLeR"
    "lHe6DN8S!#H^R^&}UELWU_5+B-_4!I4LcfgL!FmejZfU`FTBtCO?yNOjp1cmgH{VX!r}h)b;3+)RDiBpRD{r}6(~"
    "KEu3#+$=az6`#zfplp=7%jZNN5tqJ-F#BK|N|2DZEpn{s!C~EyY4Hx2i9C`QJQ_1AUMH0hMLKlDw|%nl5Di0M8zG"
    "AH!7Tz7lKMO0?4b=QPLd|%6d-k{ZeXU#NAbt#<=Tu%>Kxsy%!Ax=Dr=maHh+>{-u8<+hYeqq+iim*zrm#9(U}uL?"
    "_GBz=#kK0yU~z+HilI98<ic89Fe8=;FP0{Q192sCq}MhsZ)<kbt8H;ke1An9me*u29v~7e_7)uB{vYhS@*|?V#a9"
    ">WLS1I+^6kLuwkK{ves)G40_$@N(_pKFXYW_8bYII_xBvar+IvvhS2Q&4Ub`sCpg&sPw@(GHxHj2I^b{Z&6KF|)m"
    "!#kWz!d>J*T%Di0(`E_H)S0>Fp-^GTq%sSlZK1r>MrUt|KKvoJEd_ijbam#2G?-5)V&!HcUQnMq1@mBFwyF5;O6D"
    "&c~A;oCJ<@KB;wU5&=|xKkZ5oFh~hQK{DmD6@3kDJ0Jw`+?mm-o6dM5A>gPwDcc&TEIx4Ohz=uTxPWA7^EAwGRPs"
    "~T&{ToNj@*n;GAmcDCTi=F$#`FOUBn2C@5aLj+43YkRsfqM++dkVfCIX|m%WPSlX6<@G^KE6^0d0HQb$J?1Ibj(e"
    "3EzgOtJ{c&h*cu$jNTQON!FjZ-eHAlnct0WqSf!{B@S#!)BiH%vC!pK?HchwI(V%i@el1!cCS*+XGv;USUlf#?cz"
    "zxE({gNJ>d-Zl<iSqM(7;>kjKIwUk$<#@I#1n}|2mqeWg^4|#CIN729jMM^2`JJB2~3bcPycXAAucr&|pWDOvRd!"
    "h~x^mS4CemXsQ^E&$R@AiqG_kTG${wX>*d2@W;dfdhmq9)Vb;EiA#VjAlH<u8Q!XGZs^W9o>t9%cD0rQLE_LU^s&"
    "%<^5p%(5r`6Uw*gQqYJs{YI_oc8q=&%gJ6_6RRnlpi2d`-OwHFeAh+Qkfb#};se)_TsDFc5wo!BeN~;$QP{q<5V9"
    "pId@14Zphchfke>Ffxk$6Bl!DQ|O~|K;uPd}Cx1DGz_9>IkttE#a103v|Cfd!x8oY8t(FyY6oiMeak|14i13ESwC"
    "n-}(&pl?SO$G&A;pQ_GGJ4#2*Nq-(Y9EwtU|fx85;isuV+$52mp(BBXWvOOEaA%-tzh61G9g<xOo8$mHHLw03TRd"
    "D3e-WKF(UE7$*b3}D{wX)YZ6V4_!FUBStgl8Y74`RS`r7f*A{35J^Od8zsan_BeSAdFbiFfhW{$NpQZ1TAT9K2)*"
    "qz`%8yimpoI#^g29MY>nv;Nf~rxk*xL{}R-vM2=>pSSFpi1wtpBcPcjPlOgvP?1oTvg5!D5QIfH8}Z(Y#eA2~RR-"
    "o(k*nwqOPlfzu#MM!Ob#Y=av^_~m4%kr}nI9>j{;8{>;i=BuffAwvlTm5EhBA90wqztz@QKzKAQecr_OtXD(nrS-"
    "Z!=SXf=9hpOXDQ(_#tXYl!%#MAc;%+*&Mq`(rty9&xQ!Lia8ndSEEa9h)ZG)ojktf5TyJ{f?XmMzzda!5dRJ;Ug?"
    "&w<tQNui4lJ<z%Y^>PfgdLAXDi{k@@AJ1@FZv0sHp#>aKNpP#G4l}Lv6xV>sEBwt0VEmKN5|B)<xR&G`V@7RqcvL"
    "CFP3*BmBUd6IO<G8104Ggq3)E1Cxt*BI?k-*7<#hYWd3p2WbKA@AKXkK-cqAy?(_F%wWp0c^b7X1xztHm3#~x#{t"
    "PR(gyjQaps>*B=gl~Z8Fk2#<;IOZ*jwCz@(E)(`tcANJ$(6hEsCMB7ZN-xRDkFo7*i-UZ2GR>PQSo<E|BrBC#Qew"
    "n1K1%_GOuZ4yg1bkk%w9Vf2hLX`)mRLu{3y)~wFMxJ1PmoyTx$yx1x8dBR|=4$^(}nzWd4qTcnZ<OU9)`37%-nHH"
    "l0;*a4bm(nLIWG>cJYN8)PR#=V+FcYXKNyZ1QfQ_tA&joSnVh2m^!dg<Y?KDMHW{iJ{ueIoaM(PMy$EMwDCur^7w"
    "U2Gy56+x_A))GbvT@sfsZM^Hfb~1sEM(nYt`W3O2U*xE;j*liU+vEu>4TGSDrmO*llO?~0`d(NTrvllz$ilODHDx"
    "-!c-c=!%Wo#m5bt$q}s*wged1zig+nSueCLT+{(qzFbIDVCvyxkp`fFJdDQ!aBG+tDB@Au>J$$l4<S0ZoOPQZYz6"
    "`LGR063{AX6xT$6MmnGM{foe?~PO8izv(tM`EdNTfHnYR~<}QJ}Nr!*WQG-qph>sv;Az5f0aujre%~Xe~5ilw>&9"
    "Ys%T}X;3wXUP*E7HP!EcnSaoF@N4QmeI2MTXD1g&y?%n7XKN=6*HLQM%W;%WR!Lw^CFrzzc}=J{6)vYcoo45&!H#"
    "r$+>t(nN@!9v*tkd+%VD*Crk2jG*%iDhxAtm*XoEpX#)t+rvT7WJGx;ss3;J$o3{u5<NRiv)&HJT!U;^1O3=UAEG"
    "v;$d0NZ*n8olF;!}&~TJe6YV>xQCHcH#ViK--n7><vrpeS^ERhVK3TI;5Xw<G9G!P*|szPw%^lAN-5~bk_IIRN%x"
    "SDqF5~pvws2g*sU+YsK6MGaP=pfdQ^d3o%(M90bSg0+qO-<sX55&Ow}QD)HI0j}a1vLFnjfQgJ&i)2nn=Pn(gV;D"
    "pWwJ$U&EYVR2<&6ahQ3dois{z{Qz%~al}glk+RoHA?UATXBGW+-tY32Q2hHb-g-xkNC}{F#l2H<)zj)?($ouJQ(W"
    "s?~O*nz9>sT-2<vh81Gjn>F7ks8cp{RaDZN%KN)?wWj}uyBgr~>t;3Z_}Z?9gvh7PYC~6>X7zXJYSXL+HEjbX#Q!"
    "C9yK-4vRuSr2dmR^`N%?&1seAdUx%{<z`D=6e8~5@z=JL1h<!{a9@7&AZnah82FaOD0{@%U(y}A5@d-(@*d2iPn&"
    "#t}U57dry&l~EV9qXPq*gZSiJ#V;scD#GufcNZ(_q-wR*)i{VgWj{F-t&gNXUDzg4Sdgz{HZtcr*`B|y^%k4*4ST"
    "UJMyRA$e-GgKlMib)Q<eAH}a=;<WIekKc$hoh=b(<B+AfW36w2nE*5SOktq=o>(T=qJj2(}tl?yhEOQB=w<knS)y"
    "0qDtESASDWB;(^ev(RhSH9>v82@=aeS>s3$scvx>hQz;wqn@jH18+I-gOFRx(e=`3${IHeE%rgYED~l2xCfQSFwj"
    "V6oFJo2!9xt>Y9ZmHazqF^JL*tfA*lm{WX@CZ%sD7MQ`?OR;UOrc)}cXJ0`(I2nauq`WpgS~I*>w(wAneHok=tEA"
    "nxk(lX}V-?`39>OgwTJ1<$>doXrk3kf0rdk&}-R{MX+k#GUnynIhReJcxLB#%F=X=f5+TypWtve*bj8>l04!8Zs1"
    "Cs+^^<Qzmux0Cle`%lQ%|Q<T=()NaRK<iHGsN(o;jo2nyAGvh_oLUCppCob80gsP1K#an!gjXo&EHMZqQyUWy*eE"
    "GGR)uc@;QCSqQ&?!j28c?+_Cj`F&@KAJ6&u^vUtM_y&}IIPAQq?&UyJXzqPL{i@WMdVI$>gfqEurk^<9Lww&)I9}"
    "prqI;4LPpfJ#a(+zT1w<;@K#A%r{cU>96#m?)~{hwa#6AnjuopFJ?0SJCV-P`*0e}J}$p65B%yc<Nn?!WZj|H{Cf"
    "o7&5YLkoL9R1TRngwj+yDBM|v=8n#PK6!Jl=_t!^{pF5@f<{kL%;3^i5$Qc(g!Q7)^=TrnGNq#9anpfLME}_j#6^"
    "(x;HM;4Fu4Bo0Ke<4D{RrmFH~qGS>$7+_{L#*Pcv^7b&g*(;Y<7-!cNX-CLVFHr+h>I*X~V|<rpE%TkW^Im;OyS?"
    "7Sm>V|HT?S>><<Hj;jTN$v@1#PZIY(C`+b)CH7D+-wgEVnZ7r;8nDbnx+D;QC@-G@6mCoMFXyURJPy?AfH1Ds-q;"
    "#K!dO*(hH2Y7^3P6;^E&0JdF)Kpv@Wm63<o%wF{j$ozl6Qq$NRhi}+Q;Esl|L#EvO<#bu_jWrUZ8_~%!KK^<6@hv"
    "9}PCV|tbks@A<oCn1Mgf<}w+>K{RFFGOk9^2k5zm?jaizUg!Ibw?5#*7Wi2r^U&Hu~v+3q+48J^3bHQ3S>;Dc$A>"
    "oCukORE)}RDVog1DUY1W&zLqZ+4#;j_SpG#vc%vn5ib`z_9g<1;{5oV%XwKGYn3@{CdW<eSm;TYpoyArmfS_HaS5"
    "}!WwOMR(52G|Ye&Dxqh_Mmd4>h!59f>J9S4v)j!o7v4URg=(dZ7#KRVi$%us8+B-(<zh)0JfVmOaWqz~pQ7y>qU#"
    "F4R<v6YV~%Vl}DfSc6UN9$ORe+QP4_lbG5GU=+aBun>Ias;noo;n!C*ySNrI}TfwI~LDoUhDkLkFb0#_|jWK!Yzp"
    "^FWa<lC^mt@qsx1j90F>?W`a27`ZTKyRq;$Ck0q#^4Mxu-3C3XQ)3z7SG>KoVWm_W%&37Mc7HRtRfqAJLebnj0A<"
    "N&LXow@XXa9ST{-l|HK-Y2E>GWd9B=m5xgrqcGunW|WK9)3{ExFge_oR<3l=RqL2o=sv%$8?rA6~qR76KIDAT*~L"
    "7jWrCFPyafXJW>iKu;)t+#dJve}@P+VH$Y^8ujy+(c{N(oO}G3EPgtjR4*gC&h;df6AS={ZrkQYmC{Nh0_lnkvH*"
    "$(ipo)>aH#-J!L}-l9F>(Lj~L4QHZDz7HLmM~eWf&fiUh#CdCti)X9aJlglplIm@uS?q^!qT7CmsNMfa*jB0o5J_"
    "3G%{kuCH&0+(>0d1M2mT$e)w*DLxWM=QCEVK!p`7v3*gVHp#^fd<RIcaCRNL&>6uHO?`cIL8Cz#W$Ezk-d*+=>#X"
    "u0=DxD?1@Ee5L4x<L{K~&5oNtua_u6TMan72xQ-m_oN#`=Pn(Uqc>U4D+p0YO{(h}&P1v(amZ{lEVfk4(9W%&P@;"
    "*g$$vQ7iODrsgUKPT%TrZa@4`bMXCl#9Idb0?qY@eFis<UNH9xwq-HllWeqS*9#(?I(HT@HTXV#m#<sL8OFS#0I*"
    "@v<FN1+Z=Gm;IM-4$q?2UjvB;JDu=b<{Rz60}mPC4)6ThQfxR+uW$48<mJmB_YeLST;R$no6mq5Ldb3LjXG5-y(="
    "&LcQK~V;|znEto%vm^JJ2G66gpk<A5Iiwyx&ab%K4x<Z~Dz7dE6Yb(AKv9N65O*QnbZpL^W7COH%)$b_a~oxBORA"
    "Z!*{u-ys7ah>ySu3!z);ZhT$$TNm&EF-{l_=1$wLv)I<00uC2gE<^hv{&>z5l{_hm=yfZqUlkoHI@lt0>Pq;9K*?"
    "2!!yxDS6$6)=zJ!qp`0Sd++2@*0Ug;atJPYlR1zx?PV>(MzlfkhRVLZ=teS%Cn9)9gr9PCMHW<A=iH+V-SYPG+Z5"
    "t2p1K|Zfg7(tH4<5R>pU6Kdyd%svz97$V2Jm36QD4zdSQjSQ&oFc<r8n3*?NH(1FNc0x@TtRjT=W-0!8m20Ch2&|"
    "l}h%ryUXZbRc#)RW80e2rsi-cX>Ea8Lm#0h_t4^B(G1a|&UBn1g^#mx7{S__J&a!~<?P6xp`#-ZE@jjr7E;wbv{)"
    "@${*HDSuro{U2eIK{ItkzCSEjAwE-TPlKRm6%Ead61p`YXPxTJM&vYIbotP%k%410h}=dokfl?Uk2(7M1EJN-{LS"
    "JX_>tROixhqaD;J93nszlPPEmYGabU$v_2xZ7gp4+wKLe~-Zk-ili+Haw`U#zm|C)=WQK1ER#Gp&Lw<{CM@DPni?"
    "OKmI*t#ULyH_bsrKCR`iQR}^HV>8Al#NuM=0t6fc32w^O7LS?lzQqc&!*?3$f*VZeiNQG+=oRE&il)q4I$()r@<6"
    "B0fMwHi))C@q#K*4*fwzbH~?%Z~;brris>!fmcZyCQQ%+yJ)g+l#?6uWD*5dv>SWxfAFXl;xiTWw3QFcmV=3DKt7"
    "V!dc|avU9;9KU#Z1pFRd)z42P$Y)e-i-U6nypYOv%A_;GZ;VA*$IBI=Pv^H;DW%)c<Wg;F-9*>yFbo?RFBK*<tu?"
    "2aDhReiRljuR7Iz~_teSvUIwmUy+9ycgzVi(uLR*64+I7zrE*ddXup6%4tDtxHK6^Lw7WP1)925XS)NbT*xW9v^+"
    "lw7%sWFJuE_HNvcpjOQeo$#(S0$64ely&f!S;6EsP@jir&4|c>oNS5zfQc>T+{YHk>i?}y5E84YTL?n(?v?Tg(~)"
    "G?{^p=c?cAVS&iX|<wtDXZpTMU4z0Ld`tbZV`0&iEue;9*8V?8OJ^ZZJNMF}d50zS2SVl<3;U6FV3WthqUUKH`L2"
    "uY;-10SVuEX!FrMNQrWZIfG5|=37zl%io6l|wJbl~_=(WkXhdkhKs5MHBgj4G-y#;^s_Bq$6;BBcVA3=3a!)y<l>"
    "#yL6Ycmf*qzYVAiBiF;OZS{cT+8;M%G$ve>hN0ZN^3>95yLy;VWxuI=+mS&d1?ZO@5~xAKaKL(<`+GLcMn(~!mX5"
    "zQywBm*sPF5Q6uyMJE~$BB#@^-iey3B$H&zdf_0gAtR7<s|4N|x3u}4>bI*xuisF6=&)Dd)fr!2-#O2R9~7$V^0+"
    "42d6^p~JT?DV4@sjqy8$lMgMh%gkSmt<UTIUyGakdYv$;uXyLB12b<us<d=n8F{1!|4i<VunMB*^kI#s6mZ3?(CG"
    "m)-pzhb{|!hEdLFTsK?*$eeZ@A?t2g*2F8%F$`!N-(W%s_Q*sHMvUK`a3vX*YcWX{>^@M$Ub6342`GD2SnS@&76j"
    "kp%cK$}~?K&^G*@*Wz&5NPr5INDBYbW6?lY{I(0o{e0@ZZXH=`-Auzbg0L&cj3Q&nn$X_u(o1(|H2nnp^FjnQssU"
    "AGNFZ(MRameRQPr_fh(C-;0jngK)w9E<1o5Nt*J)J(6~_oUafa8xxqhQU^s$b>S4oIFuB=`#>U=tH>MW74@p<3;J"
    "7bFYl;Eo7~*b?##C;W9iunWc=)N<I@d3o=!@AGD}#qg(Lhh!?3*I3m6GFGw&SY_)l4hH4)QN>6qrGHM#1WK6I!US"
    "5;2>_9UWLr&%wi8df_gxc-~eh(5q#(7*ttJQ;_^TqU+HoOfiQ8q2bnS|+-z)Or`W<#YkW%YY{bOC7%_rHMu|U@$T"
    "n$-oE*n@%*4$uzOFldJXe&Oh)ld69VYKII{uMVkbf2(g}(l09zCF~pgMT}zyK+<px$)i90oc-b<-tgY#AzrnmU3{"
    "b77_>h!bB=j@~2$9XEwy$k3^w6CmXhhfR(hE_Rmx)GU>o4wFd_Et1l$ZJ#2iL+B$a^QmpV5RoQni8o4k4)NT;hl}"
    "ucaMyCtACR-khAAK0iD~z&K}|^^hYOvNJI*$yU|v-v%};iJHBvYP~?@e49^_{!OBGzKws@AJ9Eevt!GRzz3aOqTH"
    "@GrGN{iFmAy<S81dYzu-hy8QN&(_>52H@%-lr8#)kCa?F;EvLi**xkQL96e_SGpUU}f;__yeUWFt90_=#pv=?8Ew"
    "H;)1TsniE!dP2qK<~b$2>9QN$7==Ei|l~RJp<F5w{I^yQ6+!t(rzrCyP?oP%dq^Mz~(u=ZK(m1LeMfbz49i0`t5h"
    "E4Lk~sK*f^6+c`s^2VI5k19$4(Bp<i~EpM-rLQkvP3ILL;Q^^V{qlTGu6v|3K-C~juLjl?-mMNwTl$_|`J4G%s5o"
    "$b-X1LRa6c>c9)AksIMt}7f3DisCz;-l!0~%_XhgIYlnjM%fIPAffZ4>`+@6F7>KUvwQtSEE?c4^WE@~`JblBpY*"
    "zuYfM?}s?70shCi$*Vc2P}N7}Nqyn3Fc57SFWS#gtT5}La9veHcfcXZ?MpeKQd?HIk;SML*W)oiqDh)Eg|7@)kS*"
    "&0sw+kcQsP&6lgwsB(_fa!$d9}<f0j4U&zb#cx@IrkmD}m54`EAukkm)zJoo#sFshW?;eSpOywrgYlJTGuovDZAW"
    "cq7fylZF>%f7&p+YZC|eyA5Wz0-3w@*}g}r^#<CpyZBo=?u;=4zpTiLp;^A@IU>^V;zE2%vW&MnZicE^VoO0y<O("
    "2W(|7>l4~}3%@^EE#kjbB9}S2J(I<L%q3v)XxXldc`u*G8OEwrU?v^(g)ZBM>t=vaS>Dd%VVL%yv<Rkg%bGV(oPm"
    "4Tz3%@T(aKj%cxG^VZ|NLjRmHd42>X83>xqtkV{B<zge~Af5*f)8}ws&tn)?=lQM+CoRKz^`;Mu^*qg2}F^O*pKo"
    "(sDZ)P`mI)<raKt0RLZo0R_$AMLa8$>YaE&yBJn*v08GvTP1c8PO!o2yzT?}w{n*mNA-&;3?yN}4*Q%NIh6XoSTd"
    "-R#UN2mVsP<4rsweiES^w1b#H>s=U&a8250sGnqzKO99_#VG?-v4<VL+AIqjng(9-p&DwwVTV1VW`pa8APR?g|*="
    "mJsag|=#X)-B@OXqI1>^$w`L0veWO@E(zD9-2yT=1<PZ!uloV*_5FsFf^P$%2o}}I!+XQu>A#Qa+O(L*Ck$uLDN)"
    "w5x9lUBA2yOUa)owtqf$ykTr9uypbx`IZnnQ?7d``FA}$8bYED%f%WcJ*}ay`fj<eSm=!p!yhB^lT&gInBGIXWo}"
    "m9R)nv(PS;RAoDd<ocrUJ1Ao&DekFONI}gpL9^rhAlB6$gEQ-pu!$`p@t8yonRvAinmoYW+^BHM-xcIlC@)5Ld}Q"
    "fWK;wIH`U5oVnyYeD8J0gfk5DDIsCw%djqTW=BQ8g?|D~kh<cjqZd17nSx^~@_b3{0V$g&+qI4>8ZuAk^PIL0MWf"
    "~dFo+9J_9M;*NXtcDk{iXe>Ql2nMy8rz4=2E5DY00)$<NmNSdf<DKNUSOH+uESkwsDMKk%wOMl`+c_=2l1+gt6%f"
    "pgzDsT6A#hGu|6(eaj}jmhd`w}$*cD>Nlq&{}f+`ccpq{Ue7aquQTl*Bx0=XWq!XPp&L>w)xnz{QX{oANoz1C<c-"
    "y@q;dUg)z|y6)BJejb0>lMIKk1o9dLQoyFsKWI)K8{HQv+_ukRNIT0(fsGWi>n>2p9p?J$^mRs_puWE4kEZ(ZP8T"
    "qT#R6A;5s}0Od*zIZcCIh&_xnR)39Y%Uz-*3b*`}`4CiQr{2<5A;b)1vE;TUG8JZ5+OxD)LRNo5QyMj$jg)Ps*<4"
    "N#ZG~zrZQWoM!BP1Mv&t=nBLM^SN41yWblxE1!bNd*c~Q+}E3oA!HS9?x8e=iH=Uc(EY+q+|!(|>6<mjnyyrrhPR"
    "1Xp+=b<7R;XCORforaxd9h2Yq{T4F#;$O+W&op;BMy#HSB<=G5zd)u2+0m!D!#(TJWwKs>9GA@}rW;EAE)(-p~d;"
    "EdIKW`$EW_~`O+J81)_Rs=Atszrp=l}XrKV!`5oI(V@?k!j#IRSDET0?)|G4&-0=^IB(u%tdc6eOpZf6ENF9NUfG"
    "oQ7L_w3~8c&KczCbWJ-jeM5}C%HTDfh&PscF{5Sm@vW&!Lc+MO>ixT{N?amkote&DE7?mdlU%mRJEe}0#QslbqoH"
    "Zo5O<1HDju|oGvxr!)oh>eQ4i%P~4@-^;u9bYHm;YpSoLd*aA(aqcWlj2?A%&3YyiZ@E5?R!HI&pG8>3CF`VF$Nj"
    "-3iG&HLQC09fCKb9eC!cmd`8N%0m}1p(P>~)WE!pk6oD*1p!HNpY6r(VP8@N)V9lLj;yQ9yc}Ay7jQ4Kg<9q**Nn"
    "1<$TIX+_$V59@CZ|FXEUw<^zw*!8tQWtMuP=t*UZ1=n05%EC2-Df%_r2D?U5zMYddU74g<nh;0*093%6zu%FZO$E"
    "Q*x{FrOIMkNHoC4T}G%y7nlxXkc{Bs`|%q*oay>PX+-_=7MfCyj;S*xXM3NWEz_rQGxjY42HIj&qf+rt2{MW|5l*"
    "Kp;6RVy6x#0uvA6_dN{5F-->I<WD<NQzOCtwt}#k=$FHJOify0fD=I*pAY^FNI@m*?i510JVHpinMWv*b8=ehsoS"
    "grBc&cqN>!YWMS=lmH$rKGa9B~DwrcuxCHK3IduuE;jkN;lW_4}0=@P0IMM>2|5Vg~_EEN&OmAGXn5A-?2jGbq?d"
    "v-}BXK^uWnJBanG(k~OJaI%;gN_Q}h2bZtBo6pkh9T!eYrRIvZMN`vCde=RF5GZZ`47xER>p(yMGHN?TAt>1&E8B"
    "V#T}pBSR=I^kAQ{Z401NqkxS$Jkgi<G9)|Xu91!id0GmD?hb4<nMn&b*aFa?Uck?Mvf<rL$WOs+1MoX}hWn<GHTg"
    "aR;N3)wq9Dy$@LfM-B1wqQfwn0$|~Jo6VPn@m=P#;tNCM)8Khim#|nRD~L_G7PsRsT8mV(^WPWdc`)b^86j5`4KW"
    "hzF5r|-e}2PzGYyrT$_=3p$JHt7+qPKSe7!pHEs|?oM<k~O;!jkm9|CD4atWE3Z^!~Ba+9gSIn2NxIoDnt{9a86D"
    "k4{1LXsVjL?#B?JQY}1xTnoyJKjk6!jcSoEiW;%`tzOa$>Y`yHCb9XnMrQq+|eg2bP=a;4q0W`UlRx5GimgPz_9p"
    "9J7G5Dw+VoZ^P4EdJ9He*~|iI!Wy#H{Nk2$(QsCfbVi1ojkJ=NQj*w0g+{aiGt4eQd#hF1UaoN=4b`|>nH^i9E(D"
    "muULuKL%|R+jP1aaqcMh#l!Z^zP($b@$Vvb-1Dv(dgG|Yf7x#k*|Cne<OWKvc~M&NZ`S<C|VCt>k$4$_#M5|7HBQ"
    "NEz}y|f(4;C;tG++xa8=|QO-cv-^)sKaF4<YthQwmtAL5hLmQ#1SKhdu;;@LHvYci1Q3X*0Cs}5fg4xcoJJuMEEr"
    "QP)`X8iUf}byN#WkK0i7}5bzgAST|uASWvDSqdSgj$6ggcGB<8J@fDDYgMb9Pk7va+U^irv(!xlE)qLi42*^V#Qo"
    "sm(4$y)wwMV>&Dt1{4RFc7gE|2r&{&W2#xq?RMnI!XL4(*Py)>VO9MbK{;$>28jK-F{yxna$;P%WEx#xA2$jx=5;"
    "D(e7CkL-%9n8Ywf)eP>DEue0j8OJNEA4uqMMZUyn%aOv&u^VTkhw6^xy)gogHxhd;d$A8|{XD{ezj8Udqhi0XrIC"
    "T+G)|(CoG)ZQBQ&lDga_(XI!(tN2F(TWcb$pdUeS+e)5VBV3mkVWBk<7bbi^Im>^PgCfuaNdQE5w&Eig5&AV4`-H"
    "VSt4K=kJE41?HEv4C|*+#0*?{zomrcE^0&ZHdGDuL#lzD>shEw9$IeDNPDjPck{1<t+hTVC*?nboS<ls{P8U38N="
    "9PnX+FFLZ4(BmTaQY=~6Io^98Vzk$<TnuR1e2twU$i-io)#-q}lvoJ&gws``)oLqi2a$4qoBWSP3`4tTT*P*xFp>"
    "*n;O2y4V`}QOHJ#at&TXC<2m&5!bbQG;{DPw6M6~JLNEfi{4KzrGiGJa_pNKsMU4rz=9x~P1r{@@~)@f4&878u}M"
    "VyY)pZwo)k;9Oarb!}HNpzgL+jx6uO(x!oSs>%;fa*(e%$tZE4rSS}ut&X=(#kOJPDCHe-NmFMF)!QQGC*OO3t%e"
    "n8E^19>n3kLrLen66bCD>2#tCw~t?SGMFvmkP#}eW}mj0m4pencBT#cHbF(<|Kc*zt1qPBiKt2`n1>jdL6mLHZC<"
    "31l&dwf6e7VN*ZZ^3;NZb(7QHk{G2!a+oxl5iYJD(<6RKdVMey7g6n031Vzb0+7<R&4dRX#@zDi0<?IIy|^HOcy2"
    "GopKt1XAz4FEE+@k4EVU8V8@R)Ba2Foh=gd?or;Z~HT~bm@MS+Pfb$_LQJD3|O*po`u|7vt+`_to_BC^9?Tfm`_C"
    "3AQ@Y;RD^|emJ0G?R8ic@S!(Ebf{Q5j4PFv#z803b+jVNy3eOL=3-q_Hi>!XHE(c8T7hDLw)@_x^3LO@r0J<Lre{"
    "j@*q_ZPtIDcAG}n@uPI9$}@!Ok+^3St|30#-ap_V&P|l<=#P<JH*-}oxCkdss!fd|48+IU6c*t=+Yk6Zd@jS@d^9"
    "zxo2pU}&dae2v`}$VH9iOYWSNii8E|Jzi-VQ5OM}bnZ2v5`L1;Y%4I3)4F)Kp)Z5jFlTEWGw(TPJtzTFZ<4s%2He"
    "~k&^eGu(Z6K-Es<&cTTgCq(|k7w4Aq{QPf2*i01CML|Py3uXZ7Hm7<TW;5DBhbRh+Doc!4f9JLa~C+UQ>v>S88n("
    "9x1UV3=wB!@q(TF>S1|c5)JOGT6^a9F?2e#`4%O)ve#Lgd#{9W@Ms3l7mF)JLJ+t&_&}aUc6!{RNYTOUkKk6#h_%"
    "skVSqo$xKGwc}Z(?Ame`Zf?>XLbISYpuVe0{gvUd_?!IdRWu%VIUgVBCrD6u(OwcOo4Xot=m~4tL|GAsC%Tf*vVf"
    "-)V=`CFO$R4I5gay5)E$DI0-s+-Nc3%;xE8X1~RZ{NaPHaGHwt6J9nMhP?X8qu|#qoW0+B4(VIZv(|R6zQ?xe-C7"
    "^@|JL9U=kMkil2s)%qaH>Q3LBw6>LDZi&$@7t>V-97BbDF3Z}><@mb*DI$l@^Bw4m3T3q&^5<y}W(1QGB-a}U*p("
    "p4}lZ3zQb2#M<(S`>1gQ|u}Q*(2IPg4Nj&jP>z^9AV?-V*x}Hr^7^%B1l`A!;D?!A56hmXmzq0CkBQJo4-x7457}"
    "CFz>p|J07rihi!e-824k9QP;9Q?On8`Mvuk2^q7ieYQ2}oXp)lNVPY_XU1eCK9-WcoHI1)hJn47ffIg1VfzNlyNy"
    "4|#axhO~GJYbj5-e}dX#)0;Q0a?EYP`$TA#7NdGwi_ov_z{+PF5wf2wY^X5#oYBDOPX-ye^+S-F^C9clY}){1-;q"
    "mDaoPZkIRLd@=%ZYJ6!zAhz+WyMnKO)77Pfx7xIxgq05J(rT8l3pZYxfPXUrp8c%6#k?f)G)CnA$3!q7n%Ql9hp;"
    "gh8CC5ok}eFli=b{gPXZ+(CU5rnrsX(Y(1CeWB(wOgM<J}OwqpZc5mB=9gKS%qE<&DnCDb;iB*%+vuNOUj{42R;w"
    "d?cvj#gXN_dlZ|MQdc1-~RRS<7lL)Zp_4p`bW_d+Go%iWR3nE3!3I$hY5UYKdrk3Kh5Sz?xth4{5x8}RTff+I`oF"
    "Wx&~(sz77+RPVWLYp$lJg7X%AM5aDDVI#MQ_HhPhl##KZpJ6LkebN~mf^;MNUjM#t8e$4_FHJ?*{xvt3Tqvt*R50"
    "_{x611ODYhv}y7r0MxSCn@pbod$9aGND&orvBzrlS;>Frh~$S{@*gd?7b?hfH{|X{aa+TKtHhpdX;wFi@P*T^v1z"
    "aq$T4CzI&pOiIh};t)<hf*@i$*=l}8i1!y6$9B=ulqsvxbVh+T$;F92$rxw@9U6T<Sy{tCFGsMY6(@QW$T#dsXvV"
    "0Grbrrimj(?}hza3Z)q#A85!&p<%3IE`3_R6($1G>6z3?uH#_U~*xtu(CP0;;WaG1cs{ux#TKwLl?;p4|Im?Id&b"
    "B2>6figYVEBh2C!j1&W^^9gYaXwik%4fn_ZPxX!I|1wUxI2Mr_Ta+7-hYQZ7w<m1l*(nkDABv&!~>9Z9$&_%7?&y"
    "{QWri(u1<97p@SX<5QBbun-p9nVUkWsXIu8gnMw`Fd;(9;35ZcbuF<Z|q$$0Jttv`Z4(!!|1nf2ACw2%_JgSH_XV"
    "YI~0!7DMKXyWJKz>pPzhjAZeJ54U%ECgte_W!)2t49Z=<dJ<d(j!NYnBi1_eczU-?hR=B|`Ti!<2O-coYueEl3Cr"
    "G}26qo?Bw|K{>*L4{d(0R%q~f01yG<%}{($QaU-od}%|@Fek8r+OUkj6r9bM$|=6c4hZIc(7-(KiT#7~lhfhL!~L"
    "_v;raPXc-9Q31w@5~Oa|YAj(GT=hX-${w&?!(`QfYA=Z#PAed}Z}g!q0dn1Qy>f<R?TVzfx>TC%z3Trk}L{~ue4("
    "XUF3CTT%_KaaVqpOMaI3OA5X^`Yw5;f)-hNHVSphO~k1DgJGYWt`l21Il%q_#20d^r8_G={F;ZvB<E(0HetoN#KO"
    "GfHt1QORCMYz^#&wlR(u`(c!0bBp(ky;um`KnHHr^+-vpXe>cS40;2k7l4-sT$H<Yb>t$l=Vd@I$(l9R}mW@hub!"
    "M!7L^fYiBu#Bt4~3C@;FBT-m4RKQT-l!Pl~@io!ecCaah}7fATN!mu)EGnc@r1B#GHr7GJ`Qr@ONEmq!QksTT-U+"
    "RHQCOW|fvNQb%A_5uCETNf!}Oq12FQKcl)i?~<ITZ)$oa0#-EFIY+=Ld2`Md96zqfDN1J*scyuY%7i6Fg@8cVv1p"
    ";sqv1k2C-}<b6lX3@L5?CuDpcac|7+O2_Z_oGom<|55mJb@qM2+?UWzjT1kG8!L)uO4oh@kcP*-xF7xFVG6GQ)qF"
    "dZkT%*>A*cFF+(qtiFX$4AFMjTnB5RJ8tjh+tD}M3N-3#FTQvATy4DGX@KTC1|wvTFDcRoYO+c9In-@uWR7Hp<g)"
    "}RhxAz17#)lp>~E4+Vr#+lgq%U(@t|-C^4Oq24`X^U7V0oh*b-?vCbP)G^Onu)h{+Y!#NfWEBxas%_edx(ay>8Ik"
    "pFP(5PZ!h1Zx>R)NtLJZhzBR3FzInv|BM3`#5^Z=`fdOw$b(ri*nOA}F|?HQas~FhN0LqG{uO%@ME)%_U|9G=9tz"
    "#8XYndFck>$h0N#dwF(FFxyU)AS&maejt#M3C8V7fE9HeD|!YQhQ})EnLA&Wt28Y2=W-r4#z_xMS#)I1+<r60pB}"
    "*QA5vZ5ohCp(hVK#z6zNoxT^*IwX0;8eD-xi{j!Dj>UESBC$yLvmS!$2G9j-xkdLrWh6q!sD?t~*Z3`o+3mNuKHv"
    "_*UrE)F&=mzT@06QsL<27*<H^I|JhITs<&mHI7)KWc&otbhW_!?-k{<21wi@tzt;2YVn=matUn7S<yyJ>>WrJ+%s"
    "<=NP8j$xE)=Z7Ou+?FynEt6llUT)2?S)^L1}r3$kBvf>ar@a>F7Xt3Mc9t@vT!$pd-)SVwP_S$6FL9_x!dxpGoA>"
    "BQLyT=pc;p%1oC65z0Ab=G}Zx2|{;S%ei`J4wUO;~QSz6BSG+-tz9JL?;;&p8b^bQZ8EwiJrfp|$`c?yTX&a!;Xn"
    "m&;k-p6Af#?Vk-bYuRCkHup!<HXF_k=P^~*<eC9gVO`8SnK7G>wBI8#V6fT2GDhD*(J^orj?K1j86?N6DkrR%fP2"
    "vy$G4PRZx{|=RGNt6B=4|wu}_$c8@T_dG%^-Cjz>9_=wv0+!0R!|b+KxyA<1wS<hqHI;SsO1RnGEK1wVh(o&xA>>"
    "qmIAAc@XFMSvqBsa8xiAWl%fvigxDQL2LEnTk=*MN(QXg{e;GSJE>e>!eT41EL`#_9mQKbTO(O?sb3>la&9tp&7!"
    "!eTm(%=rAG$+M(S`fhxDrACbfzm^>9$TVS_KH4Ts3Vrh-)zCxZ`sp`O&>cO54+u=vN{{FS&Fc174Xra#TsT#G@&Y"
    "xKXRN&wPrM)Y|2*jq*SOV8!VqLi#c*6E)!-JcfGLr0}FE>DMq*K)hV1tu(M!`c5t*ZWzDyA+8S;<^q0iTFEYs#8B"
    "gya&DOF+$)Mb=b4ZH|dtvkVWQs7;i$Jy|@M(jM0I7NuXejfmP5(C-BHGity`ookHbPfO=~SuWY~6=xg}Pp4YN!)s"
    "jCi=C597`r`^vUIUtO-=fb$;^aG%bND8iR+H*x!XlBs|W!R;qRP`rj70V8mCL+7!bu;kMFrGEo%lVsdZ&P)Vw(;="
    "U~hhIvCa!x*0Q$EodH;i&)^CM{kl@xXMu-Cy!p3@PQ+6La^t8ws!)N*P4zXeA|Tqt~iswoKjdnd;d3Ti-#XDn1dE"
    "fD$C&1^YDAoYf(Mebmgg7ed9iLjrrC}OQ&CJ&6UszvaDERDktyYX&CNn(w$o1;_TWgrL>3PerswW9|+fzGl|JiOX"
    "=a*c5bl_jke&oP7q#P!(Pmpg{}Il>ET4nCD$6R`MW8_L)Af^3wVe(5$1E|psm3G3NlX#EHkuN6syJZ37kr(2hd}-"
    "XKkm&ty8leqTziBb?i&2P$9LBZqzipx^~qdgle)T+FJO3mh!Sm+JK}vU~8^VE+E4^+2eWOOe!kUQJ9ZnS`u%?h1s"
    "uW=RNbvIbNfaU2;VeM;L{{>oB~)9KERAUxGU~raeY`Tx1BZk==%5dX8sFQ-42Skl~oSqK-MoHgN%<pF7P~6zdjxy"
    "Fuz;Kt%2N_J6OK;ht;|G!+@sAYOu&UlInGLFI{opHQP&Ej-eb97#1A7+Q6$2jqTWHv>1v+%8@EX4Z-N0J0c{jq$@"
    "7W%;f5@HkOsB1N&1DVZ2(k^){CtSB$ZfWWbD@?zOVWo=@%Q_DC}OhHjZ_Q6!uks`czDn6@d;eh8_K%F*iD=YiZq3"
    "OCq2;wnfP=-PhSWALl7*z!L$V5!ZBs%CB91@RFEhtaA>dSG*<7}S}14zJ-e5WP@FGwh)cw$NpooYvAI$u!vR^3pg"
    "Vi+KfuYy0#X3_gJw!Rulbf`tx!Q6vbix(YqCyx`#1kf$xY$S>SV5K51mrjUz*A3EI5cVSL6~b1VtyHu0U81#ONlR"
    "CNE+%RYjqEd82<OH+#(Of!PNN@Bfa{Fv(R0ZAs_u05tr<l^cByC+*3;}6opezt^2%~8iXc+ON#|Px1wYXe<*7*E7"
    "(#ilAl;+qM=xH0P(40(wk*iLZhgL)3{i8&asmZOfKy^YWSFD*GI%fSo|7W9(t}ArL;1Z_j^~Fj4?*SF#^~OxLev$"
    "IEtQJT(G`TN2XuwKx`jEkf&Q17nz3BpB*kcw4X%12CW^r66S$0kC3pi7i6crhi5Az%Tk^I-W=b}0vHT*l<_r$kjU"
    "9*!j%V~Ji(-i-qKHMbDg(De4<4}x$;p(?1q|0go3&%EKK#$uN2iC+i3K3%G)DzVMWN_E3S*)@*}x^_<iO?zBYy3y"
    "v7Bi!T9;PGCTl#w`#1sMCIY}j7Mj(uInTzT&+UpT#i{N^DXI(%6Qj{)@d7raVpq|b47oudhyah1qYnEROi%`oH7E"
    "N5&iu)*$0pd(${Z(ZBs%vncO*RH_QuGTnNFAGs?=-HdZuRT)6&7}3h?<3K16#G1gnio>IlJVjxGlswV$z^xlQ@RC"
    "pw6UKXSv3?TNC$6n}-bDCAI!r8696?wXg3LPd11gsBH#8(vKYD*}k1G-cM=&3-s%xPwxFB|3zwn5Ppy`Jz&Fl`L;"
    "bxhFLxo|w}*O~(`2Puv<Kk<p2sC9PjrfHr5&vAL$vxuDa~$5Q7c9t&t(pQngiE~IR<%-40hInzq0JVr#VveHa~LP"
    "kYRDGaX7t3W_S299umNDN0L&3)>6g~%u|A-od`5tI==3*nC`r{tw)s3D4&f%yUbhh`a<1kO?m;03}wNg2Skk?QdC"
    "d7gF0W|>6|Vy%dHPzKv{oJeR5p>G9)1q#L}*z)v}8i#u=sa(U|>QZ-57f3btc9X<2C7Z6+pVsy36_Y(kxdHsYc%}"
    "yQ-zMoC^6+l@Y^eP}a6;`wQVmh41@v&GuS&$-XGJR{aZdskYP~`4q^B5N?EIgTqhqIA$RSSPLUU|9Cj7@eAWy#?Q"
    "O$ZL7Q%@f@iPyN&;9d5BeYLLl%hj;7k&J)EMLKi30qUhLJ?>4^t#}Ew)agGPbP`MY?`g+7=KE5AV2|ddPx^l#o{X"
    "h-D6INEph}LqMh+MP_gZp@kr`hsi2g{Z(hDsEd$%q#I44VHw{RFLmdLDDbFU<ziT|M-B5xXwnf)5EKktDgyku#>q"
    "Xr?$B~`<2JDj2qgI%$#a01q#|;V+mbCxo94O=9^zao*B#EZt98Hqq%V>|d0qIK|J^dAQ5o3u;8~cQIAWEl8W;!f}"
    "dcybw><;pcN~Vt)nCct8&JJS70Ws6l;kbxN6C|73bvzbD2w36p_+;p+ygwctKR-JD38=K|=;T34>T9+`?-a-?v{C"
    "y8TW9FZAtv)XVL5>ayNeya4r#SrKf^a%X4B8^l@I#G#V<Smb0dZtW@gZ;RvTKjD%0B*oI`KQT`5KR?+xqj2!;P)0"
    "Zfv~EG1W^4E$wtfKpx7G@l*o1uH-8P`N&2bkoT*nAoz_`EzYZ`j093RzhJwn2?*<SZdTi<s>xn=48~-GXnAOD>pX"
    "X4{lb>P5+R#Rs1xN=;`5qyy1f(oF^rjuy2E!F*i~sdSh&Jz#JR3-ly@J1MrhTN^FO}P3~>~5HAd>a+I%P1Jhn3P("
    "#Lpt=Vi9yQRyA$Z`g|loF`_6k+D-)hsRXJv@L~<k#UM2k9z?H)C8==uSTUwN1P~r|PORAkG50D0Hfx@iEdI6%a#N"
    "?NOx(`bH~&4gBth+jCDa65UOfPSz5fr|2wa(yC6558b2p4qG0K2X&h!?CTvHLyxfuHesEOnmD$=*;tR+HPe2_rdI"
    "c$XXiI2FUEJSQeI=15+hQZT<`f(-Ca<QP#DUbXSPVz+5W4;wZYXa+GTQ=#j0e;>U=IcBs0*<bX=qaX9@M!X;C|Oe"
    "4R7;2$`g<|B6!G`4CFn!#T>fte#X5h6C#vH+KtMABL?(h$NfOJWI@pmR-d>U1BDt5OCfMb#m%O5-Bov^Cws@T1cv"
    "7={VXrg@J1x(3%Rd&~cXC)ur7w?g^3H(5O<%Qgtx@zqk|3(=mA`Xj`BScuDwBZYF@(<vC8pckoc>7lQH3igCxaA("
    ";#nJgs-CVfMnc*2UU$CPn_fmPbQ4xSBvDsA85;ch=h`JM0^!Nz-WiwvAfV<RVxdG6Pn=%&NFKD(gD5M)l*9%%VJT"
    "bVdh*QCk^ihC0HGLt3Zg!;xhDRVJ|DXeaXw``VW8Eh6cl_9mek3DI@ktePWilUZ;Uk{im!sEiUVX0!A<m2CYhhPX"
    "_*=q9m82HF%MYO5HImj+^Bwah^W!fi9V`|=^HEN}UsyoG~7PRbP<f)mlOWxRir=fLv})Q-8f!`3WQ>7pG^&2em0R"
    ";mNAY?((x8aLWxnhznh_T08SJvI7EHKw8|OoBO~Gq{JxNO-XjCUU`-WxiFMNF|7}X68gV=f}p`xNnM8*bm8nR5*w"
    "$TqR*C%<L*0R>2}c4ZEcg$-bxE&zhs;=ul%WUlv{xkk}+kD$+XKp2~2K`Z?Fi3U9WJS7mj$!GHvJgm))e<iKgJ$m"
    ";^!sYEDDV%`6Zu_LaEUjgy`V(}x^lD9pBT4#m>Emdt6XtGS=p2NT3rt_=r3T6K0S^ZufzBrG_8o1ePDABFQVhJ3q"
    "?dTfI;2P^-GwW=$5^l*}_N`$1=zZH`H{{xT5KBNqTa6`5O+AmbK+p}8Ek=Og!v~}tRweahGrig&3v}H&inYs1)MP"
    "AMo^)_+7{J+v#F+=RcN-iD=KdNPL$I9M^cP-obJUKFueGkAH!Ok)@D57|qJ*U$-!R73c7y`H!yJ<w!*rezZ>?3SQ"
    "Lmf1PFdDKmnKS&9kStesl*VRa2W?kl-?^)?GlDGzcV@e>6f9=V4S&=J3dX}jD2GrmK%w;#$CdJ;_YpcnM_-ugeJ>"
    "cG168M7U8NXS-Mr)(`HWZ=Bv~hZwpzw&mh;jsp?F+qT@EIKb@#Cw}qFu9ca8M(`8M{OJIXKVk~g80kv|A{Fu+kv}"
    "&HF-!&@>IMu=V(JzN}f)0lzKOlVDk@Xn8z0SS&R}tBb0^3nLyyXe>(zd$JMOtmgi=g#QZgnT1+_whuCd`hFzSxdK"
    "iq<(>i<KqV>~uPfM)vWMMcb%>d{h{p6O@q}yUvslkj6%)2VqLEL{i0kVT`m0-v~!+K45oj95ez8(4pes<kf2ot9$"
    "<B$CoDue}jLyd=5cE`pFUTMC%sK)H}x^FMR<zQxG}#AQNEm)_tut1+!`qRgnNx5=g=jr2;HIkC8^inNiGX6^QXo#"
    "-oguDV=E+7(qI+n~Z``1sI4FvN_e>DOm`MkAfxZW6!MBS_j@pg`wJ1u$={(*re_0W0H(h^2F*$DhW|m_GkH34jKn"
    "WjL`TQleLC1^)SDG^Omk@`;Gg1YgfHSbNChtMwlT5v9UL3O+c%J**f*$_a@JlWBM_k*#mQJs~z3(!AWR?JI4r~{s"
    "WA!b+#prY91HwTwCiST024RS(R05sAJwFL$?na;%{+_2r?!IewJ!vGS;&~9W79Q3(fZ-U~YjD@%<)-Mk$$`4S)LN"
    "m<!ydr7h)Y=b5#_SOdRQRp!yDZ7*LWesG~PSgd_W6GRMhbg}dN<QT-;$VMG1M_Dr_uEL6MpB^5Z`~tN59GY;qv$G"
    "3t;$qT$N3cf<gBXa1TEC-2Xa)|#C_7CZ0bfv3D6&U__3b4v)zL-~+I~nsA0pf-93>RG;|yZ0a<GnHIO7T+Yse907"
    "*KP4$sG0t(_Wpysr+r#8+_?!G!k{QB4w0^Tfz+u;z{@k6o?iI^f;r_zwGIKk9n6j`E7~0G8EJ!t^quhjhgX9-3%F"
    "1r<G-B3j_A0J8fj1&)Ah>_bGBCW*PKq;z%E_kQ$+`E*9`K1>hJD0Qqy~gmG&ch3z|E<V*IRC`-rWlI?8s1x~^Ll9"
    ")8OV|MH#CW}W5-r$+cYWNMUs$yS}hQK!~((r9K9*xWKk_D9}?y|lmJfwn$Z3Y{fAKC`4Ws~$Iv^R@x1hlV}N(@4+"
    "lSo7k&+(F6duA&fD&C?KNgqcN$6(`RC8LP3c@^u8&B~O3q<&ZOd?g>24FUTon>x`f{%49hts<pRqK^gVWpG?yr6#"
    "l*HpV$MfH^75foli-k+F?qvQIB>5G40bqyA&Us>`n!eC7Aq7|qa9b<zw_WD`M3OSYz3g#@dvvxaJ8LFlOm1(bbOV"
    "A<ycn0>*>t}hnh^+lkn0%m}AJ*Bi<Q%(ZGyS-u(`*d)O{?FOT@ssnDS1+Hu0%doC+L+*0a`HMHBkv--F9mUm-X~&"
    "6Q_(H`k(cIA<ek_%X%4ghX6co-^%{#I@}1=!?Ps~MpWQjpaWs}8b-aZw^yx){VvhTa93IyCe<d{>Qyk-Hm8HL}kd"
    "0l<$ag3m>qOJ?E*p1{Z^2o7l$Sl=pqP|88ueVxKqX|j&SGzKJ$g<0#2TukMlI)yA(e<7m`_792&KGeEsA8Cei%$I"
    "c6uM_Gx#7mFM+j9@fO^H2JixWc;IwJ0s7_(Xc%Xur61Be9{LWQ2VjWP32OK)r+*haw^tWC<c{a76_Y$)<PvTzocM"
    "O|{&cn~Z(5am_(7cHmOg})YV(#`%*#$Y4xmG`Ew|}RHgiV-PiWO^E!AV^U8#mEw@`I4mu95ap<62wi0!gUKQ)@`x"
    "HTHJU?L%eX3N3TPPICrMgk7d<kX`=W(f`0?;e#obGwHZtet9ohw#}@)7VE~pz~SleLPzweH@^6m4Z5fRCa?X;)i&"
    "8B$1!ascILo1}O?VeurgXgndj_1%+IW(kxw8b_!<sm5Le6edy41yM>pi<Yu4s9q7iTBiLw(32IgDFIS6MV%MtrY+"
    "Mxa-LUBm)~N8c>U+HHsD=|x00?fLBPR?RL@cZ+=8z?G6tpy$9{%#nh1Q3i5=eS=)c){PLbuE}s`c%tj#aHy9FkNp"
    "$9{2XV(*!^yO+%$cjs%HE|f{25n4Ze8zVe;Ht#<|L-$yDl_+qCWJ^72-+OMB+RV!GRbpn`k5CQBHTRuPyro`Tu7B"
    "Qc6P{IG{B~0(DL2d`wMywdis$0N(DR!nEij(7W0FB#ZhmX?$V9L3s&G=dAGc60wTWcS7n~xJJ%nLjw6J2QG~ws)*"
    "rlfp<2`56Gb#@eo2qc7ASXfNeY+nR3&u8b{XBY7YvxU<-tao!)WSgbXbLPHCaK;smQdtztZ9SxWT;nfk+tCXQO5F"
    "2SGR^oJI;(nm!_UwIgS?uRbo411SU=`{Et3xq5s>l_a9yCJnBS``0^uPvz)@skJ38q&_~TWCWio0;RsjJJb}|I9t"
    "b<p*~zc)Unz6N=<G)6ghRnUw2sJUX_(DgWJ84yu4|($J3_SMXb2rg95=K>RZC4nGU`rrO2dW0BiK7yHcqC$=EXY?"
    "WDM)$<@`cR{_WcqN<6!<l&UnsN{Q7|NYV8z0;klv2II;UN53AO|9tZ1+!W_=pj&>S7;ls0mWY=J&Ns=JjRq*)5l<"
    "wUV}1MR*Bc5>#?L6;yfiCkYPOgqCQ-Iy5cb_gU)+tTxY{yT>$Ip6<WfO%SmvD3wHAAcmN^W5K=2<lGMJk1C9051!"
    "m?PzWcH(Ab@;BL(HkrBf^vSzaYHp2qy0!C-NogVOwfXY0X>+ywt`dZj7;|k=w3QG@RCVlOeEw+3)m2-=l$Bkp-^<"
    "q1wsl^ueje_16&{E!nycF3;%>e0l(VbQV(^buvBg2YxlNn09hCu5qPolRrFDN0O$Exa_^bcaM&I1`7Qz8kIYNy<b"
    "G6thN>gDkI{wDlLUL^K1mmbYMiLNQt1zL|EuVEQWA;KC)Pc!UzqR<LoVU4zVZDrf>y@H*ITapz~i?xq>uC@OeArB"
    "cE<vB>*r(B<dB=Z+|UPPy-lCJbk?@Vpa(7P#pq*+#wVD;s6~JB614jf{~E&?QTtf3p$VDQB|1#sVgnia?RPHQ?ic"
    "FH4Q+?F=;+yh{_3zdpOCw-u6vYKs;qq1t=dXWPBC=pwtS+)ke!5$H|`~T^!M9GDpaw1Rs;wiG%^4KTJ^m5aCy*R<"
    "Pc;9VAG6@C7ibh#9t6v78f;sW`p<9WshR^ed3+oCMm*Ma4B30y~Wb%R`>%wJh9BHq@Q-D+l50D1Y2mxKpB*RJlJ;"
    "NJmsBsZI7Nf&9>_k%({m+zkI1La=JQ!j*Y;L=xrLb=r;5VHFN&$ke+_8nZyFcWyuEcnV+9es@vc0Eq?>N4MtObB@"
    "+}mjWz@T1}{Ssk01YslpXCqer(#&Qlt-W?K#%0t+Y0gYY%U2U+Db~n;U6+x(n`_q{&uIOHThX_uJ;npzCkn=4CyV"
    "x!tUh-+<P%yh`Gwr;z`wSNk?4j6z^DLJgucGrv%8RDuqLe@aP5U^S#K?nmYeit6ej+f%Y=Uv*Cxg<mq+v?>sO{32"
    "85C?`L3Y-oZh??-ivu)8*X>G<TFKP@Oq*&TK70t*R)dR7u#z*1Gl*Q*(01mV@Zus7UnG1T8+T(jlPU39T}x{H_*S"
    "Vzb~l(V(MP+FE26Nszw-saBq>Exl7t8jssrb(5wFubN*QXSlGWEMu!Ke_r-T2PDxi%s@#Ejf!1$Ij10BdWGujzCe"
    "KTnn-+gMH#pQ~t<gY2h3_lgMXUc5;iEg(1*62`iQqM>st@>zEpNDPT79xWt6Qc!Du-6fQhZq%<h?Isx7zu)<W-lr"
    "(Ry2742~PpNuc*SPU;RA#LhvK0M!7*hw$QB2p0j_ro_@JOGL69ogrri>9?Th-f`>VqAfpB=t@LB|X#fkRUfwMNw#"
    "=LLSAQ^YBA`G>aPQJFMh6X1pi2$ZlahA2`AV{E8-N)^OUbRsP`C^Us`MqEsoU&aGkEh&8HmN0^`xa~W%xyJ%u<&N"
    "bM&A!%NqU}SK#qqrJSC|bvgIy!~k<IwThe3OrF9_5XYe7@dHiRR}rxDk;f=R@Rt7F;bbb^v9kY||On#szeFO~qXN"
    "FAKG)x$M|(PasS#>lq{i*Ne!jOK6u$FsxZgG1^^;B}^Ws*s%X4V)7tRp=Z~C#yGfvCugDNrEQ$TigS@-z6<+yu#e"
    "7DG$@-Fg?zIhK0hjnUrJ}6fdstN+GFpBBf8Lr~0|YP#cXH>&lb{U+@{8*eslDgr?I6-H>Y^muCI3fOv_~p9Go1!C"
    "zR{m#LO(cjLDTq~(PqYQt1LKYX$O=H>bD?0o;_;c)-O`QhpC?C{{^`1u*=kw5J2ZdInxu*frx=&J$~V&N&v#_&N~"
    "1(11dq>Gy_`RrdTU5gW;7w{A0Wr?D%Fhct!1!zbALMJ{BK>j{H8UA><e}1N_F@AoCU)9h<0d=b0b<3xDkCgeU7$@"
    "~tVbO*%*L}7_`mf>g3<*!xK1RsDqOvD!qivymqGCeTR2u{l)43T8yunqIZ`5+BPxNtXT2+8ztr!Z<&09yA;>PMos"
    "5gDsotj#3DLvuLKsY~^I11W7tL=rei%6lU<=}$8MkGYz_*iKQls{$}e1q4DvWf6n{QP}A8w2(5>Hzw^-RV6c6u3{"
    "fH>`&cVR$j7avzT7II?@phL?@1-L2Eeec5(9AWhY$gh<}BjI}t>EV!mwE)Q<Gbv=v3>VT}k+`_>c!{FQs0V04nDh"
    "YV`@}@Ff)`W_U4GjghfV=fQcGmHB7S85)mZCR1R4I8O#oB9Hu@uuZwFOfPwz!Wt)i4%G?V%claX@RMt+HC+<|iw)"
    "fQxF`K#2-~OL&?EiOA}pfH<;d&bGz*irR~WV9NxfVL-J_W}&Dhp<g$zi8UuT?;d8YH@WILk-XlKTW&uvzv;#*wJq"
    "s|E=F?|!f+N*?R61x;mU;dAQ^ez(v9ickb?zV3KCwYo(2XB6S_vQNv!!gp>>KH7)Qk2Cdzn_%>J<gt%a@3HhbIb>"
    "0Ui&V4LMJA!ut>f`ilSviaea(aGua!_(-;zq@ZdKRi3=7#hQ0(aWP(N9WO=zWi|9zsjUlXiOO6z?D)Ja&h_g0Kd_"
    "AKVF9J^UQ?qIGjBAVx3k7fopX#r5;gQ;o1l>JMq@Eih&m(%*=*}y4qU1w*(DzreD?RH<HECZV-_c+WGS!Gz4{)iu"
    "&Vitmd`Sb&`LbF?-9y1JnKK#RGcFBx7;`)OeKyK#hJ>An=^Ug1>$2wFj)zIy1|1xfl}HB=?aQWfx&q0x{~J&(B{|"
    "O=CRpM;x3*Clv9fk7uh12)*aWXC2&q6Dm`S<u@>E2xD70-{hR2U2Khm@l6UMo)Co@#(FtH&nJGZ7abG{1zE;3I6W"
    "76iRo&SG?OHbi!3g#-*=)}eqC}20mNcR39&&sN|x$g^tW_2(^82bII-t~RX;}aBLYlbQLH;<^)AsWIg64hLj0Qi5"
    "%yUqVg`colWnAUpYj>=)11Djl6?0~ILdHNZr^&yA;y@;GyBt2&$gHD?BA;b#(ve4;#2-bnWgOyb`3#{e7G4N=cfr"
    "95nBESdbpf=?`MjUD^xVI0>rn5^1QPHQAtB2?%yQJYr2p>&@I6Te$l+VmP9EbJb46U67<8VDqS^?+f@9MvqPMq7H"
    "W3f7XiASkdCp<(T;{#Vo<qXQQFj{#+@M1oUZQYj##@}K_ztJK;_(oSuvJ%n_*j*EQOqfo<+W#ua<fY8$^4%9j!0*"
    "A)T-0L;8-Y2T#9yI^6r_8wEA2jZ)xqkXAv9!PG#I*z%3G=0)yCf7b6Jd)|Axt9SPBxA$RsV7U9u_rq`h^j&S8e!<"
    "8PT`Gb+gdIt&$*>|;a)Fm+WOC&QX`?AhWMh*H?PFCJgcU*GHT=`5-ojPEd&dIi&%U72!Sm$Z-Mjkk8*!tNUk9!H<"
    "WsA)DC>xgDhtILfA_TqWis(W`Lp(jOe#L&&9C#|z2~gKIH)Ak&`%q88U1D3^>9UmIcDKUqbt+~t-79M@6#gZ93U@"
    "f04-L1ju7&r)YvV?VNd8tE_>33`qq3vCyYae$39-{Ag&Ha4xRn|?ELW6>B-5t{62d*JODj^_~HmP0`JoEqtlC>do"
    "Omtk27YmHE@_Og0xj#QNV{qi)Ab3#ZGt5U#i-(d>LF%DM+)$YB{K`O-*x~03{5ZKD|DAeOP}8WP$t8^TS^-!>;n2"
    "(A6MJUoiUvXB8`V$*DhhfpKZgwaIV>d#r&GFApK4Shh^GWhRK=l$~A8${eyK-Pkx!Ws5(;^HPrvw9Kr<FMA-i&hC"
    "{BYaT*QPLC*1D2oD9@s5gpIx~FEb9l&^Q?*T`x80!{b|&do&s60Q*RtA(SJ}G^ar<|q$fPwYNjF+{i*};FC3o~!d"
    "yN20Ge&%@%s3Ce@*NZFIEO=CizGy9;M4paQ!bLRzc{!%NT2Intw7f*dZ=i%l-K;J?bFLmT*k{~(PHg~_7I#gkU9("
    "KRE2sFNF6m-%Cs*WeNS*D$^4;H+>2hHoE`lqQ)EFVKa9nywrG7>5-QP^WM2jspTz}5qM{y*7bJi@M)cTQlKs8PMx"
    "=rC_#YWo@9gNO{g<b&I+6W7eE#BPJN&9nfWCcne)I~C@27|RFFQ2hZyix_=`=#3YM_s>AiMO!gsyY!{h*>L_D*XG"
    "ny&3zk(E`>g^drk5s|XVNJLiJ5Melw?-((88Rjnag3M$esto071<O6eG!d9US9fi<dz3s<_h{?9bPRW_O>!mSDI#"
    "AFD<gq;X*wJY%oDr=q)j8hFQY$3dx4N>5!l!U3hCNw{c!bKVSZ2RcTLKv>5p*3tWw9=JyVcwPrRe4sIexH%V7B}T"
    "x+;wtw5ZxfQfRBV)oH8<i2S~`ES3jU(s9`{pvmt5x(m)M`3%ND8wZ@(fQpXsWVJ7fpm}q?nn7ZaMU9^_mG(3aA-{"
    "3%wW&%Fc<3ZL%M7Uw_I~1PbYr1+Zk}+iX*hkVe@E$rZX~zdzRKEh{4;FxR^w+P(_S@0-tt3Et4^fx5=^h=KP@JdG"
    "}Zxh>@0iXtRB)mTE5M7L7*y;PCJ8zgMrGKR^HZ=U1=J&i-roLH<|Czfo6-F*Bjf2)aUH`%}CEV(brp|HJ$blk-3P"
    "{D)V6IQuW7DOi7l<{b>h_W}R%SbLP4IlM_ew7$Wt4m&Q#KJ^##_0W*ebbgCfEudF+$$YCPKUo{Y8louk8RG%Fr12"
    "tO72U-wrVIvoAYv%;4k^MD@f>n&fm;NmJ4@atGZ$-_Of)Yrx{s(8kI+l@{*SFGMqHA4jx{j~j2oDe<9!)vFjNU5H"
    "D;VX458FwBXfx(!k_~T(ZI({K!$dmGNC2I+hQ1Vs0W3`TqU*y^E0<jqJz82r9Y+#p^AWR6P3{AtNg>K`n<<E=n@j"
    "?9bb+0Q3OuGZMnSxW!wBv6h}xOjUIF2qUJM#B)FBK;x*EWXUZq)am*yH1Gxsr?OdIpo}~7bExvrDi~O3%v+sn@61"
    "fdAG_ZstEhV>cd}FWI!+2Lc;0Zkr5q1_`$@CS_gEYm?T+kOR-4c`D>K$0s9CMh7#J70?zL0MFytR56RH-3SMT;$6"
    "Hdm6E4F2IBJAsVpzyYmNk}OE-eD=PIH5zAk745}&k)vMin-QhidspD-Y+jH&+_IhwMuD6ZL@}H8s;lTIW?_%7`G9"
    "Zh>kZlN1{~ZrNr}Rs`<r*#4HGHkA#;gD5|TcQgMjf?1nD)P2YUtQd|mAHFt-RPps1P^>^o>&K+8k;Eid1RM&;4%e"
    "RxJ}^Nmv?&ER}sOAWJNX<jCR%_`xEaLgt2vD$_S_toIv2YP9nz>Z3;cBrGcVII)M%%L}T%aJ_t2I24EhmQc?3-%p"
    "h<578&%_>k3B$fI`9K3yd$yt0A3oH#yn44w7%;Wm?f<`%Fr+A;Jg_d}CTkTD;5YAUyp?F>OBZQ-Q5077*oE{*K6|"
    "RWWOL48eIo|(e|LEoZk1r1!TF`(=s`?H+Zg@;<NnRyfNn+CU#Vlu4z!mXpaVWQ$1dr{kpNHUWVWX2S#YYe&VzNV1"
    "eDy~>!v$Gr`<_^At89Pvm@MD;gaNr_;~p>^kLAHw@Lw3qGY$ZuB}*v8nF5+`q2<pWrlX{O+E7_vzAEx}R4r-iu~w"
    "NT3>W{U;gZoBm0CRYnJ`(_&_8>`#Na+{tkB`RE`ow|X`oF#s*Tm-t?hf&mO7Dr#AVL#1pnLw5X(RQ9Z&h`7$dOri"
    "RHV>nyspe&>>g<NX8zT1S`!o<7OCWo6dmP-aR>Yxw`L1X%*w*I8c|ofOV8-nBSPN%FLNd&R~>dg<(^iziFrlZMan"
    "JmW#>aq{OpOyVX!`TiD5dt@auQ&`l;@_oWt?Ryv7vu)NR_CFbP_F-MMbg2$N%07R{M2hZB{f!8GVx9ytq>wLTzvi"
    "H3bW1xOKHp8MxIFDW(ycSnIh}ksDIKvgV{W6EcSoC!F>9^h8@49>6(~<RMPPL5|n6Z!-UEo+K7AEAMCodWtBzr&~"
    "WYq3NCzvhM!HN(IiVL7B#aHDRG&xD(#)xsL8YzuL*F~HyB?ZJfb%?DA{XC;ySF>n8{ph&?dI&y4X=4wG3}8Er9ys"
    "ke^&AUEUB%;fXz|*{*$*Q<pyhGg_`@N(e}}`W``!hAp3h^f)?;8%+}u$&?1h<1^)ThuF0|gKs^8mrs^;zfw$mI60"
    "6Ioq5;jrvZ)nNGya>=I)K@K?Z*XdVw;S|ec@9z{@Q&S)LRs1{hs*F@(3WcsY@@9jzDvLK`GMufYLxb0E7AOoJZPY"
    "{P;-mjFmR({mZh7TI^+2~Uk423GMc*EG0ir+Ccm8ja=nL=ioy=jPFX?|u;DlhHt0@p1HJW|G#ne<?OgU|9LNbscX"
    ")+xdziUdZ^K|kbt3YYwzq#7zO?4;x)TI9rv{i8K|c=5AAByQgJ@70_!xF8(CLAg^Dh{M#VP+6JC;!g8xy@PUc^`F"
    "3_hEXrN0*O;5<r9=O~-z^dPHj{HcoE>@G3gj%$U$-S=*<_AYippSW+vt5aMQn48{p0uxssZkxG=J7VM&MoH82t8F"
    "9OG!>v!-B-F4@ahCO%_@`R5MU)Jlw|ajM8t?<WWbHg=k98#JA5QA>j;ZX1eEYwEXK0Ty<MJWQQYVvjMrdslus;KO"
    "~SKJX7G6qZ{=A!Ch(nb@Iejqh)YmaNt@^WiD>XJllA44S7k*J)$?FglzG6T+%V5dV;WW{>>A_Um6NZsMSP8J;)IR"
    "n(930Qve}L?sB}mOr{3>YsHDTvMeU(i1+^#O$SlZp$O?M&m+0%K!Ds4r#D=dqU|`|rMP^oB(RrsW+$Q0@;eCYu(i"
    "bknkGi%up1|5;?N8cM8W@55i58M6E3|DUX-S~PWL^B|_qyJ}`#N2klay(QxQku1?YcZ!@zFi8ou>0?r6LUZLVt|Q"
    "<dFXK>lB(nQT6gF^dWuJwU9B#VEY(+sRUkJ#UkvO&<oMaLdsa9)O8Pcw|*R-e6Pbg5FEub4nndp7Qj=kJVY;N!l5"
    "||cKdGl_4nUwR_1U<w+VJL@drj<?@3zXnOxu^k$Ss6^>i8d+BKdci+~c*aoRro<?#4?`0MG>`C(<L81WlM*$>7N;"
    "Qlfn<3C#S_(N;gE?3m8G3j=@Da;@g+Jtk)r2|aFL}0_?6HBUq1S$|iWUN)3aN$DR0jUH2`&QcPUwU+k8OQ1SL`XG"
    "6kv`RKrcF=v`(2kDWnyj35q~DQ<Vx|L0iBio|9?rrgz2uMhVjiRd&jiE;W2B~;BR(+_^#bJC~9kMFKrwgc2Ey!Gl"
    "JM+6fNm8&_xo@gFSW+Q-2)rM;pU;oQIM7eE03}+poV{+r<DEl0I!>L%49A%306()hj_-EL%!09WUxgc&i`6hYi+i"
    "sX9{LaAeXAIES6Ci0C&;q$<y-M{ef5t|+#n&)z39IFMGNLdg*#Uv(LP>WM0<P;V8>A_88_%OHeqBTw)T*Rbq+PPm"
    "<Jnn6g(b<girk5oYYZdAQfQoFr=_!>F?h1Yn1c#Z$Mw;MZn1V)u*NH|AvcAd2LzN>C^OC9P-W9F)@)>T;BF-GI#_"
    "whu{BT;6hIz)gm<QeG7s|15He-vfgJ8~!%lq3@BZbsrPRtna*g=&qKvX)P`*u!>PjeMz#sq3h$^3Gd+{t`*tTb|%"
    "c7dxD*<Ic+`>8q}S!tv7N>eua}`1N=ooD=-Pq{humOtn9H6AN6My~_6I2b+<4H*f9GceIcb-_15mflCs?6oDdcVk"
    "+$`**(e=uxRDGr0S9eeX_V-QCW|N@r01$TFi5iBsKU>ZKLf6S>S85(v!8y9iP5*XXBs9RL$zXL4XQz#o&2)%$_*c"
    "w!+yL7dvJe@S^!~?@b|}5)4p7MXUdc0C8j^VhH<9%#}vpX)a)qWY3~RFfZ8GkQhfdj4WR*aAdu8mM%~gF#3B@v6("
    "F>W7q^%|Ly4I%la`$BGO*w`McHPFc8kVplGg;ZM1hAgZR|Y;BNzf2%ZKTI%D}NZtcVsXa}v^>l;D^$+YBJ>#^Q;F"
    "&x^(sv7kxq*8hN!+Kl)yA%!m$UEP9M@tQga2^$WWbd*1Q%m(x^nG`Q|73{j{Nrn*e~J-dy|~*sRdWG;hVZfM@434"
    "wfIacURB}5_-ebWp)b}|Wfv_@RPbai1VRshE7b!d8C4?5q?}*1^Aj{+hE$y=zzQ@4!nADJ4gzjqjxc}<U>3gxT7$"
    "H|+^@MDKbzwjRzKy&8-0l8w`A1|(R1QEQtlV+{!*O0BILs`WE;V?N4sje=1Lwo^`X+RTx<bGEUJ4vGWXvt}a(jK^"
    "8^VX(amhU<i)4P4OfU_kjOHt<c#IXAe_H{aOkm!#l9qYLh7abHNRp#MPN|gTZv|+kt9k1~^f>xJ`qu}7EXS_3;o9"
    "1#xX*sXv%68{4GswY(21}*Ui8m&K_i#>B5NGxzH@3*^u+5X=5jbcDIRCHx9inU+Yk-<il*x4)J*=w2`xq4&JQ-FZ"
    "6v32Eg19xi)wn;%480rFCBXq30rJ@=UroR#hvP1eh<nE+r!;YOQS=t4x`QBo#S#BGQnOYEJ>`Tk(zRj^$}LmeJh<"
    "Hkb}kQYL<?T52e<9bm#TdxoOBRK=i?+V2jC619q|xRynJ$EVGA{#^hqIsH=3~beU3oy@y(M$l`jH;c{pnG+`g;k?"
    "*cVe%q1~PJL9yh4$9(RN0@>(T>wB0jxQFq(BZ*MSYZ+H3%~gN0*`Qkf*2m6jjkS-82j8_t<vV$D-N3>h)H|t_}Tm"
    "!iTWBdlmoZ*kw)k+ekF#mlw`REF=I&;%|t+O=lA7H(L(O3#_k6;ApR@YF&#<GAK<bl^S<B34zddR_Imt9z8sK@II"
    "xoHJX~QyB!9!Y1eY=hU0o6r*dkeOnhn||9HB)ejo8<$nzxPt`hja<t;*{?a{7%x@$HLkCqexQl^$M4M0=_y4&thX"
    "*zd}gf(f*w_p0k8B0LotA62?#QDTJce+QV#+}2d2GJwtQ;(vPQ~yS#EaOxe)klNF3lB6GXKXHgM^k3!4x{1)R!4a"
    "6&ZV36CNeT&UB+35=>O%WP_UzEcdt`>;$QMa+r`5fvywt{-f}E~QbtY*nz|t%NtNro(_3CR3(MC!o}H?8mF?1zj?"
    "fn>_i8cH(q~^qspq4cnF2v7fgRE-*bdd$9yLArI6ag2t|SHSLuDB7St`Q9gx`G#K2i<;2-fTS@4nd$k3%#aMD>8@"
    "T6@tSZO5KOU+=m@wxVvpDujIB-tcpVNdY4@<Lhr>Z|HpeQ7@SJ!Yg}tMSEi|I8B>oZzw3mZ0Blbv7v9Wpw$r%0_0"
    "zP2K!wF&*IKkpOg`Fs^%sdMir5vN$l7@S&k6s*2T`sM7BSKgfX@wejlftc(xM`S+Y#i)W5nxR>=)@{Ef{Ho@Da5{"
    "FR+e_S4jLadFTG+R>jyf?Z^;aeNxh=LH1>^rHuT-H~nbfODuc?WYv{LTuUF|HiOgnHMp~@tg#_J1~M-TyTR8;StK"
    "W$n(E<Y4}z6X^bo42c6XpKT0Hkb4o8fy=-9PdN;tr8)6`;Glh+r-yLVrVOwl#xA!O7;ar=o$IPM&6aEx0J1yxG>7"
    "?ya!7ax47V=?BLmjM7HURSQqaSH)l(hNPF!dv7#{0y7M7qo(OuAFe*kXEJV=JQi2iT5ZEDAO(-HPzmGarS1La{yL"
    "B`0aeSl=7=%fZVdiSxGAqrafF=#!DXI%o-{05{W(#odHCygY^Wx>q>bPIQoG)Aaf|V&p|H5X7_5wB#e*M8=vWNMs"
    "k;E8|M??dopy@p+!lFx#qSx}fJUUYId;2b!?`Y9$}wtAmRjSm`SiCcc5gvq8X%G>Fzb&4#d_u9r6h*jYfD`s?Yg%"
    "2MMc*!<Go?k**GBEa0BxY+r>Xx`fI{?~5zhhg{fkN=O+mmA#;+Zk4H3eIgFgllQwx->hgTF+)C-BzcxmU7E=Rk&c"
    "Wfd$)jZNcIka_q=8pB?*Z`jK7Sk8p^{XA-)Jq)*BbdoqnM7k8%ozONg?c?cn=)m!#w4Cx6jn)CJn!K~~|CGhXyxm"
    "VI}Fj}5Qpw+?FM7i2WyuelZM$p6JoS^9;bF&=`UJc~!<cwc#lRIfLno4q1{Ay0HKT=dn`GJevH_qokJl^@K;sy}n"
    "(9@d`fET0BY12)&A2){cyI+A_Rwq=~C17_25_oNNe6T&`vIHLFhi0jiF$S<=@~`1uPfR`v`d5KLV@}C5p-hz(x%F"
    "axm@-QouI_>c(&xQzsWbZo#M}N+7v~sQy@GH`Ws#HFES|?v%y<ejN`MhyB7^FDm`xTr%)=ArhpWOsESOXotTi_2M"
    "GAgXDo_%T&Mm@+#E6SqBt<owJ|ci<f^p#V>F6}RHSXrCe3FU+m>7r7o70yJ7?Eiy3FJ+Sl+vl8IfgWlG8OTJie*@"
    "zCY_#ulrdKa4S<LtO_G+Ki51Z3ha{z-4QHsxi^L#NM)jXOp-H7A^1Z!pzW(OP`#o=W)939=zuhL;*WLs1BE<?@F5"
    "_*WYdG@3UdKAm$rNUO=_2U+7NC%Oi{z|e@+{)Qx^3VZh4i?J7CkUwWG9LDk@5TI;cA!EQT>rRL($z>91Z`P<+mFA"
    "JxN!BaCehl-^kVY!^O`1=Aa%oX5D-pm3=D4Sj&H@b#PGYvp1kt)s2hu0E+5OV!iMmdF^Ec@K<SI04pYKc^#?4&m@"
    ";;<UXA7igowVnT#rW(|tM_Hr<>S@%7xZx3{+so#M@t2#4^d7jvz>*%|1j5QBVW@XqX+EyGi|_w-LaICJ&(_-DVrw"
    "-qG_)SchOQiJP>3!c>pLg`o{+~%yAay$}jL(FTECoF2i6N)>RM`gcy(G33!<=Z-{Z^mk^5t)<Qwp+hRAyL&%H3vj"
    "tFjV#F=+CYfXbaM%Iz@;Lz=T1jgfg5VCrFvT!dXQ~#a4`t$uv-VMpl=@=lJh>!mfmZ_M<A~rGa9VAqyI-KM!?u*J"
    "MuOc~y{txLb#8mBkIgTgb@Yn(PtOd@Fensy)|OsAG6)Y_`T^=?lU394nu|*^=IW!0LSW+-T1Z#K03SBpA^3NtOnI"
    "0ijn?|4yp^P?x5lNs;a%r9SZed)GBq4;(VVaf7HiL(XG1RLA<s_$Edri+BaQ_5%t!At5?Cy-aDl3C`6;K9qkOvZk"
    "7GTI&&d6>L9rx58nzF*eUpj;FF^7#Z|qrJ?&;n4W-4x=sRpg>d>d1rOr;n?eVj?rHDL8me0gi<41Oe65G$n>-z(k"
    "!htC2l%AKILbYe56)$J^3zhX%-7Z@Wyxa{fU*~SD%|ed-OI)ltolnUCoFs0=u&U8b7Sh_?~`J{^T@LuX3Tclqd{b"
    "Q-V{yDPsrSBFzn{IQ$OtdA=IOv-b_4%VeIq{<!N~{WFCkC?N%!)m$~Sau1Vtllc+k)R43tRUJFuR>0C8rSFjo$xR"
    "<DTsZPfxx_UG&U8ggJ|4nzWo#^f57U9Cul<X1R66QMRDsDFd&A$|TEcB&Iwvf0e;=47(iTyPm&ia>(>9N6<KN(26"
    "U$qj5#~DCt*5|BQ=+Y($HoRvnKm&)X2HSBANtYqP(hggT)C6v3e62VUyIgJIjs33ic{~f#4w5S#CU7l`h_z_a83)"
    "W`%!gFu8U<@3k(r<x3Px02wywa^Emc%^x1%}#aHWI8poS*KC13bUKs{D@fCTvv!k1$c<pSAKD9J<==B99ZbAYfjM"
    "4#?RAM2sgo6vKQVE=tshorl90M<v~W-SQfI@*&A2E2<%zSd#mgX%t)+QF~Yts!M*d(k1f3b+^<Tdde;FiEoBr<Tl"
    "Yh`*)VNw%8nt+Qou2tU_BuzZp)=Ir3-!&m#mUk*>tj!upvQZ1|<@{BwoZ07w8mx?-+(P|J61#>`M27V9RuS;ooss"
    "`VZ3DA$fK0SF2WcHkRhW=0`e*fV7=$At-0!4r74fx2>i@zTo|3vr9FZ<rX;p=m0RDbBrA77pv{7vr3-+JrC{?SXh"
    "!++|HgZ<-!L%pRxd{ggPej6O%^V9to=ky-^r7dDI=iliv{bhQ7c6RjBvG!bkn0MYBAM2RqZ`<52M~A;kd-&&8Q*r"
    "R~{_#(TXT#IO|9EqFrcc$be(KEG$=Nrq&)^&#z#N#b^WR&H`QYT$>z9Y-J^i(DF&l>AI1E_W1-p7IvwUo)_~7OK("
    "JSo*|E;&4pByv!;veQBEI40;Km0GB=Ci;KIXXT#dcFUW<Ae)P5Yq)}dVKrUJ}l8G-J8dlOsqFfULT(BpP%q8^#|z"
    "9v)B8lr#i3Y0(2&_!8*I^NE(G*PT1pqM`cU59L7@fr{MHqjYz7WnHRH3gq62Z3%Et3EryxC$#1FHHC7Y>?Zmh?Mg"
    "nv;LWzB=b<pWCX4(5cp1e7aoa)MFe|yu>a-CS8lB=*I)+FMCNy&;ETVMm`1DzYon;1(kA{%BfN^<K^9bTJOhRhr*"
    "2##Z{?Hyb9Dl~9=lMB!qyK1E4<{H;$<_WmQV%m~zf?6=nz&Mu9krh<xkWt(gmRdBW-WNqaSwXWLg~JLvVxqxxmS`"
    "qR=8NTB&`aV4-Y?VTEb%a&OH`97^xeJgg70}wW!t|YuZ9EmWea0LQ!dvRPxEb-6hkjuwmCfA7hiA@xyQ-$SA_pvL"
    "v<?zK?0&fXiBX2jS(8Kl%xn~rR61MOoG;dXr)-ngP)-ca7%!Cf*5k4xFO~{jiM4m?QU-pp&cO3vy)%>G>IsF*NG)"
    "}L*TM1$5@|)Qif*9H5T^3{ef?j4@@XIM*N`n2(y08q(_DC7%`m^>ZG$aVjXR`^PC2PZ)Q}QRaz@^Jd+YgAcnzWdp"
    "2JM)xaXXT2Y#$_yx5bD|{1X5+yv)Sh1S%X5u=pE1^H?dIBp%csN(s55~r$fmf*oU&$0`9LV(p&;g;pOATIWX|kDw"
    "Wdr*pRE~kgIln`z7x21igmpH&&f{5~mL2j5+=K>(2w(4fmxFwgWQf5JePZa|u23~$JHkI*A%0<q-o3#qF2A?0$7$"
    "(bGO41WEl3vHq=d7HJE;|>u&KNI1bwlox7C@!q`GvH6rrxx<{bAm$SdGJ40CB26k64DEQK*-S2t_}r=W!9_0Xf3+"
    "wneWQc*Szpv-S8lUJWl7!)vMgwS*@+Rpp!@ibSIr0u3$bd}A0M!?d-+aRDuq?H^jhv~aD4V{-3vpc1c&`y$}xEhp"
    "<V-~0LAxVJ7m-!hkh*hr1RpO_=iryfv|Gpp1L2d%`o?`J~;jr{l%q@}z0i3VJXaPB^2taW_FV+t66~cuk6faS9SD"
    "BRMlEZVmXFY}OCkT2lguj=B1y2lh0pCVbfT@xF6>~T~TQgP|%5&}zs}rJG;q`ou;mW`cyIoGOE~6LSH{W#k9+lc0"
    "n)t9QrIvr0VW24HaH<d}k}SC;F|Y)FK1ry&>D3)bjdxNURomj0&|*Lhj6wY)1q0+JicXPkDKUJWRgTJ-CBmJj2`H"
    "i2HCr<H02o*yOrE_PQn3yvu52qtLIAJvY$I9Qm`Z<33D=*b*Gajohy^m146p7g+;U<sh6dv?R93}dOF3HerZF8Nl"
    "S2d58tp~uxZ^rxqV1}Za)p^U#VYFvF@e%dvNP3s^j34R0&>)eM$`)aP3p+Vo3Rn8(nwHOX(owEH_07pIjpz(@`VI"
    "-T)rdKl>|O3xAMV`7DeN$M(5~7zcPs$C47#0P9hTmD~g2n58OvFl?&l$If6{J`hx^6EtA=dX;ny(3@|uvTsvo@`p"
    "`r&MnllZr7D!IR+dVaLsOhq<2je<G^YBt(}0>#CBiVJ1XLS8np4)Xey3a!JaM0D5@47rda0$sD+-^QR0B;-Fsp=="
    "4W}f-?goy-h<LfXg}jgIxzJZ8%p;BtgHSPxWi#3TdP6nk9UXO&PI@&;MZ`>`c7eS{S&Bd505b+H)}enPHb!zLBOh"
    "td)C&&0Ag%@r*g#!Yy-&Oeo~~x5ofJ<HxDT(AS&n(&28~+>!DmV>EBz^SSvhxwbd0Lvq?Z)-)+ivt(kf4_s_=b4("
    "%aHT5hh{OGeXzB+-lmm98x({=<!C*s}CBq!G`CQpVW7uCB|QzQ++c<Vwk`2!U4}kh8$<QJ0ID@iWnpe>Fq~Xh_ur"
    "YXz&@quP>-Z`6+ZSxg|bJ#Dcx|Yz*lncx-YIM+<I3Oe(Bj(Dy`C^IHUXj*x-54(UwnJJJC8`!Gh7hhxruQHiV<4`"
    "uTNMjLof)nCx9lDL5LLSdOW?Y0{Py-V>Yiz`qULED{R^_)*T)zviZCVAhu_AcwJ--)lUi{!e(=d_YET7#IWZh2ax"
    "X<8%SGq-jC?`R|@@l*T*v5Tl?vdDipU>nN%QH4G&y^)-#^~Doo*<hQSUS&ah9iwXu=>aJ+UM5Br!jKbOdlc!`#wL"
    "qhVE<O6l$IFz>sZT{#flMmY0YDIe+$3OiKUV~WDCw$Tjd}vXum?I*F{obj-_+6zSQn!dkFCaPSQ2Wxb5*+cXfzHf"
    "`eA^;j63bJ8a%*G^cS%+D*E3MIkElRWS~j2rFmY5)WBEzJ@9x0jVG{QuVn6A+lN|CcL_4WjG~^*k+}I=t1mfWrUD"
    "Iy=Z^(J}p7w2%8pLLyR^7t3-p0Tp%i>SUE*|HdlcoFLPijXm2c8jTV2&Suc8?aOq%72pfwP{|>&A$w5Pn!fMXejf"
    "SEIKjSDM5q~kBA%icG2?Y0(Z{c9^t(iy{JO8(((rofCf}4kb*}K}dNlD?MH6HF{cMnzfb?LBCgK#3FD)almw@oF="
    "2fhajo|H|R>gyHg%_l{AovzUh2;YqG1wki)a}Y&vi+Q<3wz<s76_X(t5Re`<%7+;`svw{Jt6ey@@L|1^@4CC+cc1"
    ">y#cBVcyTI4FY1u6kgm7FY{~vpA!`#M^oeTe!iS$+p@Et&slY1){4zi&s$Yxe16_T>!l2pKu7?Kl#02Tv?Vif-Ox"
    "6fDi>5mzJl<ZCJI-9ZxV5X<1`}Fxf&*{P4z1kd#6;dyBh?`+Gv7`-1^BGW9pzILQ?ug&nR%S*exvX<?D$^W$3w&X"
    "MBVcdC;n69XSbbx)f;$CVy}cgaVF(pE&CChp4&SfGtPd`_ETuc3_;`VINNF+J5a1o;<d~*I0Bi<`8*~y#8ZqZ#b^"
    "~7a0@`wJuIEl%<qY_UPIBx?YF^i_D%{H8_dBQ?_}1fy$8FU&QfJ|&_+Z2V%ZauNaaYIX$1US+cO{qsj?q_;BGkJ4"
    "OXIO^<M1}AIxI?To>Nmg#$t6@%sE@vub@>wVEeN{MwthBcJgnp06E%lrOR?fC*~4{CA>95kN+VpTE9m5Y<*?Sv{|"
    "Zg&d$wX+j2g3Z3L@xKEhI3WM8(T7v&^<l@rJ|=WI0G&B8@y51)=1uG7dFV!K}l9<HHRZTeauU3)E6c+-Jsyg_tbU"
    "T4%4#!RbCH(4v3?;_w&T0U7ll7M5j=o?02Pp6F25fuxKvax;67-a4Ba-I9X8&wp&vaFV(yH!wq%(v3<P@r0KVRd+"
    "6;wJee_1td58>lnHFTqD?Y~6P9#R`Sdb`U`7|D8K9z~l{-k`=6+(}8pO0=9(zw%j)Q0z(P>t$0%TBL^G!6NjDsPx"
    "@{p<@p=-P}xslXUK=eOztB|%^xI;Cm;O)HGiv}4J{kQ{n`Qwn|{O?`@(x2`PRs(JQ7gX#qAgz#1>-cteTD?9y>1B"
    "ot}HK(XoxPwM~v)MRp&JcpuA`4fhx-EpFY(J6n9pu+yITc8ni)xeo$X?l$<;aF-3L1uOW=(ea;8UhnOX#;=cF9qb"
    ">BPI6^R7pvQod9kdo7P9Zq=6rm{zuA?dn3R16e-Bl_<NsJ#3aWW1eSg=>mr-Ib)lrSY<|GeobLbSxDK=#eTRewIs"
    "3;b&>$I)hf!m(yCQAMF;(8W!0h^wgJA~bL{9F6>UZbYL7oL!xo+VnCkpPQeR0t)j54s51XV|zN{{jq5C+Iri`*h="
    "8D&ZxD`5S$|4jY+Z=CSU!)YYiPdmQJopxH*v&L(=-CYfXygOUqs6<op`JkQQ<^>Ai77K1!zj~M#g><?g+ZXgL5bs"
    "IO*lN!=w^jOBun$Ajb{djAh9g;eny*_v`fd5cx)T+d!{<B->!KR@o3k<7nu@5afg~T>McMhNfT!Xvu0?M;zi<%;e"
    "wI0WbR~A1M1O;mvQb*2cy0gXNgR#y&Kp^&PW!|DU2k)g>xp1){rEMy<i+K%tgMM~WmJ(_-N~BpDBT^vyWV$$q0#B"
    ">whp5O_pc>Lk$yo=K{4aPs!)~N-C_Cqn8XcU-#4)Cf26Gy(KTNAthr6j$ySWTWalH7TF-W8Xil}d$#<Qtza2GjoE"
    "~k(r1mu0+YYr_#k{<8{BU-0`8=~nZL(otMG^_FMu&0jswcmosDP;|ocfj?;I{MU?x09-e;Zc{HwIGaQ1&eSc`HK>"
    "xp_s1&e-5cJgTo?qH~>zI?a<hH$R54!XgQ&yEC>Mw@x;ul-^Bp#W(cpdI_B4Kik0?)B602ot!AnVdy$V&k1w1|(@"
    "!_jB~$v%{DaZ;*rV2OXga({8^LMymSa``3<-09+@HGXX4=KZj?88XH5P1D>`L*^OFU`=AU?hSTUnd;e$x;L(2N@w"
    "I`@Naxk{>P+X{P?$YXkdzS)~>pr5%5`>=pH9Z|pDMC)Z8`9pWPWMoJEcz(0+Dy#HSe|lE+RFMxA3Pc6heq8|2_Vc"
    "LrSx(y^dy5_78qZjW*mV(}>-XuhX^*vrx<SsfPqgm3*v4n%n%{(LG*lrQM$&jt>@FD-6V=X!Zk~^1o3W{boh&xEq"
    "^*TEG5j}tZ=^F^sc7?V>%l4r(oO*@pu0%Smu7ecmyeul$iOfuS@#$Y{l)4xmtU4^IP@r$SpzGui8yFIDmZZa5v7h"
    "^d_2t(RCD|K-a(c8^Px?m4^-OeknHOY%62GF4l3nf$%gpf;1_S*hTf+T#FExz$o~evMmgR?`X_F(YaXLb?7md+1X"
    "uc*-$VQub|AO@#i2zAPJ>@Q@WeVjDVIIKgCKuD=-kRFb$VEzUxcMR9Xt0tE#w0~j5D`#mr><a)rwZYROM?1)yHBj"
    "t!;u>VoF=siR=>+VjJZ{XrO`K38g{a*3B`#xKDxXVdw_wc)#bKd#6t&V%@04R`D^qU+<SJ-89ufC$ZFHW^E8FSj^"
    "jcp$iE00Pz;1mkc1o{VaA39%b{T^I)?QBkY*>-hfXtrT_&8M>xUJ&nwfcGjMwiG|0BZ%1|EH*~G2dM8fqDh=PD;w"
    ")YB);Ce@|M~7<N`Wn{?Yc`>325eRtjiw9UnF%H`K$sI!ZqU}IMwG}cxLm>OH8TgW88FY`N9RT(Mua~|Rs~1Mj5b@"
    "ML#sBD(hUVAUK7J*s%wD9f-~5iWQr|iotM2g{})nuvy19e*UO}U?!p>s2+UBh(h(U8i-Q)|*A)U}VRu5%zk5AO^|"
    "&gQoOJ_TJpgaC_)uyYO5rF@FS!L8D6n82R|KHlU{rLAz%FDMGZl<?O~x>Ty6^8`2h!edx)is=^`2*hm2Q?DIHZxn"
    "P>8dHnr&y1@GGd*;UZ+*F<NovitK>^kUD~lQ+Q}x3D4yw92CT7K}3>gEZBU!3)pDF0n;h|Tf>r`nf0*AuvFRg#CC"
    "(U4H?i~Lce+|v?MnP<~~5!SAw00dk3d(R;(^z)76Bq{KkXraWyd|<*3t}WE~+y7XxGWOttQ2S16Elr#lIc{l<*l5"
    "CW9_2DMqu%1jL~a-lNgc;V3f86$iz%OU<ZkFhC2ZZ}MQnTIf0T<|jl@cK_nOf`0$)ZlgN57p8p+Qf(rx-e*ns7c^"
    "^?vu(8T`Yw{MyZhC1$j{jL$N^TGsLqwD-09qY_=X$rG>h^S7$U_EoNm>Ig>a=AB&G4ta9z%_T=a|J087$wYNW_4k"
    "%{R>yA>hFm6O??%gctT9Rm1Vs1wz4gS?5z-OnhjbYh4-G<3GDQqxCN?D_4-g*AvFHh6ZqkTI-d_~TkPze}B6Yn0e"
    "KNb1f8Sx~vC@LxmywHPjs)^xYrOnmAI@1D%%(3c(MH&~L(72dEvC;@2k10Kn@vAAD1d^HPy39zeGV3r_XSqVS79e"
    "UpK!XAiiEAFBc7?1H{BfcO!;}=RC?u)N6_<NIjeHqmq*r-EB#)pd^dkMJb8UKh5r|1Ut;cPC^r%ejF1;k@tdjN?K"
    "2aN=C$z6mnvMn@56fGZ;3)(sD}7+x^K>_y?shL3^>+(QdGl?vvimoq((dD87=nZ3Tx@npY7a(vE@vfS5P`30z#0i"
    "FJ%R2ilxtWR<{#5ZU}f1T4HMtYnB=0?puRefm6(2mQVhyfI9Ns%k~0;C0aq<%SUGLRXddK)M}3v2#^=!KG|Be@Zd"
    "8}7o|0NifvsfdCe&A&4SWa)E4wO?c&Lw%(br_7#fLm`tQr*&OV5e#6Czj>b?T1odP*Y!50l?EpKMx{(BY6Y!P86t"
    "aL=Z<vY^D1Lkkz~8H6Y3eug5H-Scx|GqITAk3Be7zL_YaLBKF1cF3?7qC=<h&DAZ*5rju(ncEME5Ey9ag#Z?4zt3"
    "$FNFS}&zXf#(*FT{w;qO@N%U|J#yRB4ZH=8L+<zH^08-3V$TYNJ93QWW!dBri{qOE7k--7Muixm2VM`^cX7RRYDM"
    "K`FEpx~7Cb+kHcXhJ)mLPbmmhx@PIya03=G5F~qt&DWUl2#)f%->j}0!k%?2CvOu#`wkJ60MbzHafQzM|hiAS*H("
    "r0#%vlPL?Slb%l)|*HjFHMtQsQCLvYz-mfbo?or)FrwpKFzk4LW`EGTj#EO77Ag4&GuspZaMYV$9XLh+Mpv5<EGv"
    "0<Lk>^Cxq%UDeV<H0cb0d8vF342mI}aRbwYm@ZGV4H~H}PBuu$<*~*F<%}SK?RzoC>GQhuXMrI2)8tNEg3`0=mX<"
    "wmm8}R_>wRBgqCF+hz|B7Hd5)uKl_)hr$-CXpbeT6|Ir&^UZ2Sn2QQBa=S$%O%S=_96KR`@Zm0q)s&kYTA9-2E{5"
    "h^JKeXbx1gay!$v{Bn%hK5y!VW2#6knkB<N@CR>b2VIY!?l;L6lJdcdm2_X2acPef2kvu-S6Vt&LhhlXCkWqh*$z"
    "EtROrVFFn8>Tgb{po-)j~!P+hQMc&ozH-h3k4r~AnNYNfRR)3{z3}+Vl!i}B(SyfD>{)E#Y%vzh#{zvu%NQ*@~v#"
    "m=D8Rq{4AHFh0g--c;Nng3>j#?jV#0@(6+vYL!o!2_e2{)SKQt6FkS%k0T4SplBaMd9P><^^H52cK0ZftaGHWwVa"
    ";VAD50>-#g?UB6;rNRsxyT{o3_Kx5fcnk@5(8)LgCPPwnwlQZ99-2bIZQaW~5)xCc1DZF{<`zxcHZ%B6KVCAoGUW"
    "r{;vVNo`zYJ&?*;xlEHbY*7#SL0v^1ax%4U>B1~Sjkwe7G%o7P*lA44-jF#{7`x^mbA#pOfO+u#lsTtidfZHI>cm"
    "9Q$r@y-_Zh<QZ`0d)&kos+B52~`E3>=TH2w4&s2+PVaep**!Iv6DYN(VOIhaZ!4`=LqnI)CR-sc7Q@!Qx;+NSq6Y"
    "y4X+sK?o<Eh$I6okFE9bZP^n92u>zAb<wSkX5JkXrY=864z0S?M#J{I4Hh%h>!gSvrcL4twx>4cIb_rxfK|8npl#"
    "G?!(Nz^sahN9K*9)Okq{F!hX-B_2x=bGZj|=allHdtK)2{PK}I!m7|nx&9%J-+l`KJuc|VS$|v)nPBKq4yjOkSQF"
    "rxR@T|nr<Dzce!s=jT@5n0!*Kd`DrLn25DZII^yi$FstBE7|rg|QS0a3SLe3kkpzMMrNT}dC}i@f#bYrXH{Tf#lz"
    "yTY&I8~v^0+x#!%o0M$4NAGN(T`OP8jZuN{IBBY|=L#%<ag7)VK9`)|Mn~%P!kG7GtE#*(3Z5uc&}|mXXsgbH0pJ"
    "cBls*(#r|(94h5h@u!c{RsPK%zGYt&y4o*oS(m~};cQ`gX&UW?a{3=Cj|Vl^*}CVF1T5iT;L9&W06iRm62W3+JF-"
    "A-YaxTvp;!8`4#!ECAvLh1cqHe_I(;bL?16k_)H1kCloOcSm|nU|lGWr8bBY#VAUz?DO<c4;)t8bR*R*VE$m$6n3"
    "YoB*`a&bQAZDEa&GA&(c`OpO#a#$x94nMGfClKIm+62w;0syv&1`YhDu3E96M9UKOnXt`(@<LD3`8J;Keel%0!VC"
    "L_TUX$#MS(<-k9!2_+49;hA4eg<H`%rLPh8>Ff^{gzHooD@L-^Q|!*kcq>bOv;DTv12zk|#I*-K(x|NCW=Lk;_2m"
    "%0ma&R|#saO74wdo-eiNZ{NPpF_ihfxtS!j|Bc+ms@B#UA*odu)od{bh)R`8pq-?|K62DAYW8^keb?iF$BbS%>5!"
    "789?x98I|1E<{jF03{>Jbu`knPUnB_Li<p%Q+T)LJxrV;BC{V0TxH3{iP<rs)hnG{*5&x7c#2HM121F9PXw7XiT@"
    "2SkaYK}R2T;Nvs-Rr`dPRy5**EMnbh_85A8G3cdU;Ks($&CP?0V&&asHmG?Vn0^sThW04E2rU^bu&K;A5lbOzBPL"
    "SoY-4&$^K*LDQ}~``G)cpA@HzTQ786qzCl|6xRrZ~_$ZCkuv7sH=@kp2<LIe%>^bA14ihiwGYc@~$VN7SRlZ|O8h"
    "FN|1WjOJ#;lgKxqByS;wl1U;76lJb3PAm=cz8Fq{jgy4}j{x+!?Cd*oozoXB>!!$rBW<Wcuo`yN!`VQ$wU43ilI<"
    ")5~@Msq<qsMI@GF^u3sMy==`~M^$qT13IDNn!jvRIXy#k&a;~pH0cc17keIG;M-5az}lp5bSS+{tf06S!JJ)crf`"
    "eqA0|qI_Z8P%5;r>nJoiK=eG))vCd6qD2_oW~Rgr9l0pwkrU-_A;Mq5Guqgr!WWOF1bjgs=KIA4}$(Pd>PBzu)%8"
    "z$BQ_p%#4e9p^O51*l5X7~*GTLFd;cM=GxJfN9K_9MfXyg5Ahw>Kl$NOnb@gBw|$dG;sw7;G3_%{as$o1}H)34>Y"
    "A7a^64M$5J4<O`kBk{UAd^%qfyHH+oM64+|?$wTr7xfXCz2r9c+Ee%68BQ8s$?$6PonoFj#S4X!n)<AVm4M)+66;"
    "D5F%;q^n51B<VsW%YkyA9Kb;kmR{j*)5gmuMp)`p!1smNsixdTBURGUq^-SaEjbOvPs_3jLW)!C(>ztw3WiB=WH;"
    "g!e6PA$&I(V`(<<Yo>^Lf}Fo10R18}ht2GkS6Q=}1D5WTRe2!Q3R8>?A3At3O1+#U+`;75-g?>iA+OVNRY5caiL6"
    "6y2H3M#oGt8e_F}p9?fm>|wU{q9H5|S=l@SiLf8eY)>}P(70bzoc0%*zNqSSqN0l(TjXfv14izmolR-dQ}zNFFt*"
    "nu!C`gGz&`Qfwm48d{rSR#dY69o-V6@Psi2F?u!Cjf4(Ff;_w^=XkZ0Q2B#1&hR;(`_HPAORg}_KotgzFHZ*U^&~"
    "=mUs0mZzD%t&LEN^L;aWZs~yZuAUCy>j8ni;;#668+t&x+DGjYbe-`i?n%5#oIoN4Rs#AoclIzU00j`{SMnl>w1k"
    "OP27gUG91qgh`BnQtc5{xPXR2tp_iE@Gja8=G=B*<o4Fuzgfp{hyVm`&Nt*Ne^hRY_2slocR_4NN!Ozy*77U`Cu*"
    "7$MR8X*K=Ms%NO-UO+SgFdisb7!*l_xzMDpmCBs-Ow=p$jCEQwv7^KNQ7#7`H+oq%WhH76Nt`Z0Onlf$YtmILEAK"
    "WyWuw9t;8JGupwkKofWMgatS)YuHIkmI-~`IP5ftwpF*Y1D_~DgBt=BMqqhUb#YL_G+Cs!~LMTIP0VF%EFLQeIQN"
    "E{#|;W$MI7?i38>e+WTsfA#7J(U73fDO0;NK|QKbZyqK4rYZ(F$lT~*t)d$jK+GsK(}>;ZN1IFHAEmMXctYi#Q?x"
    "wV4O0=>9+yUOU&EGak((c$Z6WSxMC=8wi<+Kn7@ckbnOC0WlSs20)kep02*uLG9~n66AlPZ2EL)=y_L~9Xko3S5E"
    "atyo~$xrdCs$v`Vk@`a$H&iPr}rDEAMbNyf{W;11zQCdz>2sN&bdf6x=*DYd2!>leIU?+UOaxs)o}qE<&sOZst7#"
    "+!Qw*_F0+g&e<yq?!s51=v^$l6TZKgQ-~FiqH5|l0hp@x&CJ=NBR6PJCYv28s9msD$p|$?MNK>DydmKN93#(R?S="
    "cC4>V=P0Gb{`o-z<IY03UY>NvpZU_U9<U(s9QCck+NPPxNVs6IpH0%n9w`bRvSuICS;5EGvH+A`%i_x~(cq&<*)W"
    "vMRv2OL{VA6TjH2)hQRf(*Z!(N=>$;7J|Sc9A6mv359<ZYVg6Y}1t$dJ--O5&R0FF)dN8soG*@+lm<trqp)5QIid"
    "af(EBK_8DcrbV*MH28hSr3I^9v6M`~I6PYUmt()_7gj;Yy9<&-o(P#`8sO5D}^NRbxGi%rrg9ZiJE}#Q{w7^2vRn"
    "2RqG-+gF;&bmbSuDhPLRXENj`G<Ul5^Sx9(XOCE~-yC57x6iSu{kEW(Ab!<IW=V5`!P7%=5tmMEzW_8vk<M;_&wU"
    "zOI(TeD7t+&C%~|lLoY{FgHH{ppF;TjgmuCK%jnHNOvD<y81z(SL{eHx`}o$Q$Z#`!q}gaSUr!SZ(1O^zQd)Sz=Y"
    "UM!aK8n^wUoVr=%aGhO(uhbLyApYdwTV3j(`XUC#g!i~MS<^kC-XkPmWYC>85Skx)2Yt>5TC_g9s4uiHUejY3O+q"
    "p29lXa1=W1l`F=7eVA8^rh$GJ<n~coTehCsF0~GU&E?;UR35j)0sntM{{vgqNz1!{f(?s3bayC8WLMzsQ29?l8i<"
    "-5D=yHs)IKW3wrm+u!g^E%G3pe^y>x=DgQXD?k!&a>pU^oeM(-omc48(eQ7IyX(@s6BP31tKCqIvy-Ei0%64jw{("
    "!vyhh>-8h)_d%Ng|F8Id|<~LG6G+Dro8X(HoEB=k(V!PMiWT@Pevs_l75%%0+_HzQX`6lVA|>hW6WU#$Me@+r>eK"
    "M3~W)zV&W5a$`CT1V0sVeq~9}Se6>6-8A#_Fd?TQlV@9nYh2}u13%GHqFqolZ<t-umQCG_PSwk{)5umL+J$0R!_!"
    "i%;mR$-?Q!<n;X^Pg1i2*kUP6oL&@Vt<+AGxFB2VpO)P2x9ezBNMu`M#X#_|j+CJ;LW-R`P96dhBPx?XvJp#*~4X"
    "$eYMuONE!IJ-_cRJ=q&@rZh_1C810Za=6RNu&Z|s-mCmki16m^~Ou@QCI2Le)$n_QsI3-T4!yC0d9)_uD!Ut^~#Y"
    "2>n}eCS~_gpl0qXMULpfyv#qV2DK#x%xA{n|OefY06S~e=5C4Aj!@*&8@Y7GD7YBQ%qc|-5m<a~L7vQ|ED*%lpGs"
    "?Fv%!r#MpeoGQ83jboHtP`Bmfz@H+_4`(!z*Zw$eAadhsjeAHZ$@mpJ4jMfmh5Rp~6u;<M>WXh%MQW5rz;gY<?Y("
    "YbLnR(3rET&#UFkn7-Y9mdG!Ie#mHA$56m3BnOQ`-EQ0h2N9s*X#Matz`eNkr&Wbc3#>+=F4f>@gJ(HEN7JOdL=f"
    "$6$dyMC-HDpw$&r|NIS7%?5JHE*ZKjs&-TN+lCr9PY=VCLP^|j}(qGna1n>8c{23m-p0cr<nNCVxaz{QIq<6iTz{"
    "2V^}?^bv4AZj4kP@uv=F|+ehY$zzs=6$Z#C{Y>;L`JGDOM-zwlW}}sgr(+!sfLmk_KRt|H{c|aqM@m$VKmHuoHAG"
    "~JDQ|78kqWA5(WEbc);|sT<=;hL&=G~-h$A(5vKU{-sz7Gw;y9v9RZhYR%7~6(z|dNs>L=E-d0p2R5gxL@z;!(Y<"
    "|>fz1`H!p83&9i6?hOIC7W--0f;=Ph3EFVZI#n>w7??q~?|sp)3#eLgcBtbFqq5>G)>uy%=HjM(ui<>mM4;HXP3z"
    "DOtfJ{T6i12|A;<)wjCK6Q!<3@>B1SDOF|V;;P&`{PpxlsHrZAmR(>`+-E(yvZn_t=C|lP>q&UBo-M3o411|l?DF"
    ">7$fgerv#Q6!2EFK7<AMQJC&<%!j;R<$4OQv|hNMg6m;jR{yvbwJtfz3%>opAyzBB@_cTq=3Dg=ygw_o)-C@ld=M"
    "lYCq@k-ko!nTCRfG9CfdW$fT<FO#EaXLqxF<KHdkePa=>gq|<v`GAm-VS8c3(hPLP8%BAHg%7gkg{RX^+5ggaQ6}"
    "IANns-SX5ZQWxcT0u&{<wPB1{P%1$0pu860D6`(5JvK;YEIgXyZIC%MTbUZpd)s<SZ^?EE!l%%~RMFJIhepRKi%U"
    "p5oq0|SO-l5{>?SXl;O~GU8DeK&e<MG$MnOT+@xb<e6y7~wp+n2>s4>p0!m8T49|I}i5{U0L_%ASm3gk6sToTrnF"
    "vSz&8h{xDc9g(mwT*om1&dR8`eFAoGAJ}@)-qnH>2i?Vom1#I&j?y6x<CeIGezvJCR7R*cOv8c`M$NbT-aEFn9GX"
    "B1Oi5uT3?8ah6Wjy7@-W3PA3+-%NR?h-lkg|GQz;~-_RL1k1E4d9g9axUdeT`fg)X*`iCd@(868nqalSJ40>*=9)"
    "dkjybg8HnI7f}J_lj)cOn3#<JOO&IO0S|?F>txHET}63WLyF~F{us|U7cYOdift`KQr&1HnRCPMi`F9?Oz|v48!q"
    "YTlEl{D>6fbluvUGAPMhs4&4nhmL<T&!|@CO*PGP^%mFQX&Lo;dZFVNP<UgQ`0a^iJs;D-s82t{D4WR!Dhi@=1$e"
    "*n?B7oamAhiI|#jm`7^waBCBfu8GoVv*LkVrl8d(7vArGRY=ha#x?4fUnZurgjs{xR1Bb>xkdf0M(83T2D|l>13F"
    "BAE(I1##Dsc0FesbMfIrSz>oNi=8S0wV#M6Amv6%00%MR_DQLdkS&G}8$Z%I!jT|9>vO{-j0Mzh^Z|k~#rIQoku-"
    "%VYYr$fEqYyPn%$AMfL~=Aa%}zyQ|1#mcTZq(pLk%g&4U7cA#@LAS3~a)!|@l@d0D%>bxWZN?y+S^CS3;<f~nKI6"
    "b>$dJss1Qp&Ybs<0?DG*1WBC$-O-X+2<#D_M{Ijv5YAV*pQu=fV$n5T~(&khR9_cQbqFKZbR*U)cGoEUj_Lh_@~m"
    "yb?JY^8dzWxWD#g;myAJVH$mlEkXtRKVX~SZGI|toB;Ntbjgtle?gM8=8Plws13pkRKjx+pGbLVoK~3bph^s=YD5"
    "EjW0Gh~I3OJ@Mw^?GR%OFzDY;;xzoY^LEkvDLCwOVX0v7No}=z*^Zu-<B4P5f$Jj)plGvr<CD8Fk$P@Kp5QgkynH"
    "N2i|WhHq-t1yNj-wvWo4;oF-f<hbz5hofOW0C4vjQ~5H%fts>!+)T>ogX;}GFvI1Gv>l$871BC|5|n<>{V)%IHiJ"
    "y_5_NTA^GaBU<26`OP1=Ii5hB4B+fS`V6DH|8#XZtmfY2c|sfWt*lvPVMQiZ)?jwG6(c(VH8D5ofuiwkiypt3rrU"
    "d88#iz9|Dq*>Z+z#<Br)ho_O*So0)?JA~fMUV;O<_)rmV=GUAp*)>L$C5zG!TGK)o^;v4=Vo?;y1{x?KnI;@nb6N"
    "ljksVP5x@-ImsW-g3d}Fib`1~u#Hmy1If=vAUD&VcG0z5a_YjK+*b}|6y(}CKNn5aY3QT-2$;Bwvf?K?r;q1xRUq"
    "r+}Pe<M692$|Y`q?kV?1Ln3sh7$&OIU^u!~+t_l6ke+2C@LU*~ChMiLJfSU&<a4>{J^qu+1b#Z%TTkdpmH;OEz#t"
    "70)sAf?Yl<-GwgcS08opgd)v15d{Oxd&lnyxQ?$1^Kt>Qz{LfnMMRlhQhhB;4*Flm^}Ni!aRkDh;JWE#89TsGN#B"
    "Mfm@~6<9|#;v#5BWxB^KOY=GJF>G~DoPy%cg^%Pb?^+1<aTWO_IK_!p-a!%4z=4yb|3K7+s3KCH`u0n0Jkb!2yxo"
    "V>(khW?c+H;OuIEh?j<aUnN6^bit;0g0+30pF@1ZxQ`DQ8y$X+bXT*@sNXZQAmMPDx7xEDCC>RYZL#c4Z1sM=q*Y"
    "&CqNh44kFGOpL*diZR6Gcv8V(@8r7eh!n`(A4Lw-HfA{EM{?U*{1%)x$71RL&iw{T?*y**Fugw!?RRN0@Ew@w3_b"
    "#@9rCDViP$$LhwgD*#mey~KSYb6C_36MVo*f?@og#%|o&yyKgo-WR4NkxVqfbHoj!m3KElmmhp7}h<x5<~DlPpJX"
    "PG7${&Gvshc=ZCjSX2iAN)EU?zd;xAH|^T7oOV>`HnuSds|+}Kwll6vNRO`S>pYs>5+GE;3%j7g?Y<|2L7O7f540"
    ")N$e_UKk~eu-)(8T@Y0L~mwBdS*O+zJ)k=mh*kwUS>fzN|jt)h}<coWY<&q#<R^`n>FhH&Vt0AH`PGPN9vTJD&~<"
    "c?D%#j<5w;Cx-pz1KA_WO-H6^#*l`<bTwiMzDgIEHdzNa4+F{oBdT8T?_IDNp*ym1VbIXy2QV+*3|a2o)A7S*8A4"
    "63rbdjqfgcf1pFE78&})5DOTANNSKHkER1iNGU^I0y|LcU8!Q4{S2g75M<&2A$BxKA-yT8Iwof<~->pgADTzB6K;"
    "d|yJ!IFf(eTlSG#m|K3WBsO(Q7N#!fm~k&#=Rx02;`gJ&tUFZ;AP1m&-P|_R<dwW{c=#>!sp+pNzFdaZc4`WVgi}"
    "8rGLy9b;i=(_mtc5pNLE!idU@8(<A0mJx5HZ)8cC$}twaUo1A%=LuTvWS#xzPxrs=axr|$C}$>$@wJQUQ~dadDa|"
    "d*i^z4f_eyg>D6c5&>tTfw6j-As<5V@=tY{M_s{hc0SPROF&02WAQs?VMU@yen5X$nY$g!AX_=ie{g^{fRIeV>?H"
    "jKbT#@t15wyH>)DJ}*icLA>`ZXw|kYX$@NVQO8v7}PAD-FkD+iAbBcrDOe(<VIHIa~M$HEU1KeC+M$EeqcJ7TJ?^"
    "`BgHZ%2h4~Rb9)h<Y?PfbmqiD&tgfpqX1<{eJuerF&*Ao#-4oVVfkkXqXIM_yleCLO7-Nko7_|~<z=(y)(dSifRv"
    ")pv3yZ{LyPBlOLR^1NR`jF3V9O0;W;n6nJ8^s18#T7f@V;#};JxiKo(}FN8D;pzgDo;14-a#b?PQgeRx4^}y~VSv"
    "nn#Rnu7qVZZwoGLKa37dL}?Q(0UD5#fs)azV_2o4dBBIM8!ZF28HCpCn|oA*DqHi2P39o#xxViF+gNy!UH5gZH(H"
    "9ZbLs44zp>CZM5ToG=y{hkeqTdj+syX{$BNXvr+ky#QxkF|P-!xI26+PD@Yizv==jCK;okAD;b<=pUX9T68ksR%o"
    "^Geu3FUw}{dMf6l><VRW_A=eW0p@)Q(a$ejN;H=U9VSV?D2KUTYL_Q1x^kZ>%A8;+z5)+027Ngcwq)LOJJUsa3JT"
    "lWhk|9WAt;Z##GQcBDc+8<)@{240un9b*w4CNa$~N>Toq@FktZDL#_sH$m0Bbvw{UgoOk5lk;rmo)Ba8nAP-YAk4"
    "M3D4!eIBNmHAo)nDEY2Bg7LDhQO#yWBT)A%LPZ5k}Bk6*uw1ac2W~Uy$FpefUZ%#Nf*K-5uOaajP~jIuQ_!-jJ3K"
    "QS9`FqJ%QcpoX|kaXAMS^PJM(Bb|*hpI9{J3K`F3yhGy)bbc-ol44GF6y6z+C;BV`HqD^I#Tq(>AZFEh1vaV9$Ol"
    "1)<>5yEJ&)`tTedkZ>+@B0hWiNVYv<><8U5@BMAQ?!2;n}-gbHm#O`4h0WT31nZqykCF7TCDiFfThXVr%i4Hz)ZI"
    "shq#0IsP2G7tvhC`BsxW{$XeMSUd@v5;3(tSYqN0ffI?!AC=SFl*uvMI1$xi5P1IP?}cd^@2bTa1Puvkc&xZr6ft"
    "EE+TeGt_Q5%MjQ(d4iTVDSd9m48S@LO8$Bku(n~%JDlM+z-7ZVA`2tnYC=ph#qfEF?*H(`^eGio0-(1&IO<QAb+@"
    "}0RB0&;fLurnILTtXd?xMohuEsdVi@Y6E1g|CY0JOv9W`?egHKJ$DZb6o{)cMVfvO?4e^C0%*3(2`*1YH~S$5m<`"
    "k7NyC-h=|GO#p3mA$xkVXj*ly;j;>K*RS%{kOmSa+N3N=80x9wE+XVlQhW++oi^nepZ_Hq*|C2>X`!7`_T@Sl^gg"
    "z`DXb2?hC8TWVWoo3eGmHwNQLCiUG&}@9v&S2(3H^A-)`4NIX2dreqk(*tGL-1=im;wEtpp@W*BBHE>;=3i25-#<"
    "F?h#a;oZ-CYTW45d$C@GQV{$AZvmf6`jqpScT$?vP)8TSC~}v%fac7M{iC+&>8mNdBVh(#7?5vREKKOQv8VkkcMV"
    "f$0@M{#Ktaqt(BtBEp{rw3QY+ujVB<E5r$#pAU6r*F86W+1;U7iXfN<^L@$GODh2u~3-8G8le1*{3C^pSnJvApYV"
    "dU$a+>tOf;Hd5f}(faY~TV?_JKjwL&D!8O*$G6`5I(^sk{iAoJf^bx8+*FjYzBa*r!VPk-oVK>sJ#z*}S~zen*<8"
    "&!(6UMeg>CtiCCP66jsBv(=)Q&ZN0L(jtIx!df6?5GdxUJO;v3;(T6T5g?zd&8sxhY_U2M&^J8B$;?(FQgN??wuQ"
    "$wC#;q{c}_HdnTrb9dObN5AP~%ng2H!Ow_*hdI6T1D(&DYc><Dx`NY6K{8>MC%R_h@wOsZ3hkLNW;9?0D5pawx+R"
    "aQ+z2O6+s_xuTwmcEmFp}~m|`7UFh0)XmS6udRE+H;0=+JBC^#s0T2|0s>*afae+RbCpRL<}9X^hD{AXPZ@K=Sqw"
    "sI-S$ltmoWWUnvRG!w?IwDGkxeb%u?FSxjj0CITh60LJJjx=6anRZhgpMSgLiJ-5A9Ca9__np&nbuNK8ik3<c{;M"
    "_*;<J-&z2N9SW%jgqxhBrf1)A~CS?<sBRpk%o(3uQHNsaYaEw&G$Ij5isH5uYjOJBEoDa)T#1to{nElq4XvG)Li6"
    "bzLOjr5^Jpru;ZMfgj2YK`MYX&2evHSP4cnC*)^1@}ZPB(}VKu1=V4}k`_0S#~`86_Pb4vYFWk<xQ~9e7$GSydAn"
    "wWvMN%I5V8Ls2U6uS&AuPKJUS*|P*%hgSbI)RQcm}2$XH$R)><I__EI+vr*hd&bn=xWs7nBMo~rBWlW-rf@=Z$1G"
    ";FUNFV}%lKouNNvxLZ~$jEB~LV?R<c*Yo9RY{uqEf!4!H|A83y;mnkwjimaapgi#dYg|K;#s7c;yQa7*R>AtGF46"
    "rF4@E@0YiILS_lMnV7Po#_!KXmpwF<7gVMYU@Kx1;*QWT$ms}&Vv&%V%v&%Wzq?Y!K=z)XC5iBfHF6j!qqh^NiL~"
    "=@gh{H;Pt%}o=YD*6S6^&ymX=Qjmlx)@$n3C48DYhKw>G!XW_Wx}DeYtn=YV?8}WBAZS^-?1KFG||kZBq`uNNW@v"
    "TsTa*CW|_ihf&d@U^rFP*)beCyAaiZ0W}}#Cn&ZQ3hW{glU4`W^3VXtXhm4Oh~0}oHq`{bF=xNC#qT#nksupY`@;"
    "B|H!wPPNAe(7_~^Q_yNF{XTsO7~FX*+mttc<orG9-Tt#N|1x=nqwtWg{Geq`R6D#NdhN|G)yXJ|05rJz((hImls!"
    "7FZjmc)cacb4Iu8$g2n-n^d!x@*97#57lqfsF-2_Iv)~WL_-mtHrwQ<}`fa<LtCB3#tW+tNTE24f`E!{Ed{jM({?"
    "syR0=tGUnJ}E{0>~tTy0JQ^R!ED9uyjks~(fE)MR;?4@!GQ;%$r3}Eb1c%xG#2Slw5G#IRC<`Zvd?TTGeWK!RD2R"
    "3xVW_oHc1ivm=2E+M1Ize3m1Lu|(gMp4p$z@5_2+yHm{gwqr`Vin3P(nCAWa5J<Oj0>bsSy#-TPHTDd?+xt3@<9H"
    "CABBuKu|7%A~jyXv8aWaA#_nlIwJH9x2r3Zh%D{E7EFz3B%T!r-0GV2^M1BpY+wmEp@eoAvGbwpFCYddF+Z`sLC6"
    "?45wWHLqLoue6y!U!+A`Zhu)C?@WP#AA@n8Zxa4n9G&9$6p*kPPO0(&$#;NZmLlRcK7IyMnMckYI63dR&ColDZ>F"
    "w;@7PMhOXVIXoY5^1mja>vl)=er_$iXGj8=PBzwBzZKZof-4j?Ne|5kzOVJJI<tUgHR37jTSJp@d9D`4HvX5-)?|"
    "}b}wW0t|W^29q0LQMAhGa2QZ}t)7Hp)*XSd^c=zb@`gU3JR`kbXh-i+-cZ2LRes$M)>;H)T@s)v=J$jt|xx77F81"
    "Z!gE4SJ(hdQ}6Ecbf!3D6<Tvks3=-JYYqe%mH~%K99va`M5~AFAb2q?mAXP-aQMlD>}U{?4pO^J6P5h`m$Rr3egm"
    "5jsArd^1$SpBl6-Ft~zvRETr{jP-I=*0n8iGdhM*6Tn1;E*d$t#j0_Al7bSI<ftxH5^S-ZyQ@|=JP}j~cKgnz33m"
    "QC^_0Ci`PN{=u-i-R76szaD3e8^5WNV1Kx(+-QSW%~;AHe-pu6mmfdHX3?5l#Z-9A-vq8oNgS2`$T6a&emvEA_cv"
    "i1wX$}7mL_+TEI8nJV7@WY=EUcKt7`uB4Z?9_+_YBI>z;TlE3WGgP$OA?g@3E@Fma}X<iT2lX&|2Djhmi}*#vGK}"
    "c`*r|7^K(V{SImhvW>g<k$ML%SwC)&Avp{_4caJvfi{3v*M%Lr(1td;P6>_RV6R8nnkQ_b`C8vGPFl2?U?o<M^OI"
    "$%$D;%3O+DGKCHY{mcu1n?mS*{Qx5kD_ej><B-1bW80b^<pVSig>hB5gYyRcX;!FNB(`jZ|^>xCOP<sn?6;5+ioo"
    "GWdTGy9bYB0mkGR7qL^>-Gn!W@{(Ai7ofkO)ryT<*|@61KA}L0E%PNL7RUZvfUP+WAQA&SgT<2CrW;m1VXB*SfdO"
    "%r8-;nm+KeJ$Vk1MHJD6?GpopwDG<XT8O>T=FCm4aKv^}ScH}R~`Zncq#?~0v3(xD1ZFla!Wvl81&63ZmdI41~}n"
    "0J@Ppi!f7g|4G-6uOMZuqtO5f5()eb&C2X6fcz($0$QKH{yjV4kG`UCybH-Sm=vtXhBw-`h6&D9F-&jLq)ny@{Mg"
    "UOz6*11{(3`@`gpsJw+rAsE|!KyX{c}3hVq}K4|+i;qjAW1X&y5Kp(5cjQb3BN$OHi5aYW<G{7DxiyXoz+;R@s3|"
    "N{mJd-7RDKxl7=jb&|tbi0UNGIn$WjED4G&9p~AZvJ1-<L12JMBnTWHg9WNP2Ul2bOOh%&40l!yKg0WNrk3c8O{c"
    "HfFoUDkKVN=CUeHN_qVD=_i?qi_A=e)%w-2u4IkEG4<vgn*A91=`5(sL&A+%{R|z4Qc9Ecwop?@nSleYTS7Bg$o_"
    "rB3cVw?V%;<zH&4a`cH;wQId($|spXG#()@5TlQ{<_RfN2Ua(K!3aG*I&qft9&wb()(lYYN1Ta29R%!q+==$*3$m"
    "AT2tf6PU&X_KhPF3KC^jy2YG$5@l$SS&EPG;D(P$s!a9&;vKSu8lU+;^wm<78?tp6mFQnSv4=Db+Xt8Wl4e2s!sX"
    "5Xf!7LTyWH|bed;_FqO53^f;~R!q{JBjCmIXM0lY!*%6F?_6u8r;^&oZYbF+^SZbDOMLe;5LMN{MfD;edxPo}V25"
    "vtftEw_aG0F<q5WVTk&1xCPeU#y&x_@KlFQ>S%E-I#ol>l|xCbPJKXqZ}RP@QQZlgUi;gLT&{pJm%Q<DJEQBbC60"
    "=$KM8mQh?8nr2fL4y5LK0W2$(M5F17lvIjN4cewB`!9*dU=g7`>$0dCCL~iC&lea0YH3Mf3@-(BwM1OB>@$~YlGX"
    "orV0<-?fbFx8-*1&ZRs!jVQk!P<fWRnCkLorx<#~WXyVa=O#jw4X<4$4P_56eSoeC~lbo;YXHDYdCe6xL>&)#<5b"
    "&bi4rnE1weVf|<?XGp+TMg{{8`;}8^y?eUJ6iL;MenaukoK#a&3RqsTiea)<d!EAAji03E^YbPJSlB`C8K`~n!Hw"
    "TUcZ1I7D_EBupJeOIjE;XJ%H0n5}7VZ7b7YyB{aZgDFVS~mpbF}awM%`u}p*YNlFFSMqrb0<^XvdC9F<*oFoQF$j"
    "c@Tq+OPntGBM5idb*X#4&~qHUz`BQ?LYSJob+>+v7uE3M8S!b#6U6F?zs!dbaq4S@@;BroX)HrlV&Cq5|0LG%3HC"
    "XgZ&;d~|Ym-Ow6viLiXGNR}FnkfvjPW49$LRiXgc{t1Joc;+uZj*drQ&B04wGmgQ3mMd&4X!NlO(&%);zDms2%G1"
    "JClHG`Kx!}Y3RUl3cZgokt^&GaB<vK|?;?tby@b7{=)Yx3Z9v6npSW`C0?6!3g%?7@{H6%IDILjaQm{o%HYGa0^L"
    "W@8HPkUnn#g|@)c9XqaK@Na<0qPr@Bt^!Ha~-zP)UG3~B^5>$js!Im<`Gpf1I*)&<()O;Eeaon{1Z)y-K4dqO1M4"
    "E05H_vJrZvZG$2d!Q_(-iO(`i>Z{K$R;%1zx)d&kTbjil(=Y!ENiTA>qt@bxNqi)9!e=p9+`ucCh11DdrE+0BwN*"
    "w$8v!!uc`x4r0C4Z91E{KV1Wlo9yCz}=IoDJ{Op^n9=27Esmol1;l2o2yGWhp2YZ(hA>slXz3i+%O}l<gh9XdUZM"
    "59u=pC%He}TrX=~{dB#Uma{Q@-GM)iqQqJhbU{L0bO_x@zCy1!=`Y)?`|TEZA-My4hnv_p;>hU8&<$mnJx_8fL><"
    "Dr+WMMqDYaz9TD2Sg?7cZuSz-$zkW6;dtR~Z@uY2Wz)+{G!N$NlOO!`|aiBnHG@-iy@9Axp=v>-WfS*6Xib?6?2v"
    "?Lcb%1FdODQX|oQ<<!Ju9UP@fl0M2LMV-Uvu#vZb~djeA5`^Xa`N$sQhem#wvURPmkKCYQte8}O|xw`!e&k+L$=&"
    ">Fs}h@Ajl|#d2{wRGPLiELcx&nkla^njD=9FDL1%%TB@EhVk~1I-^RO>Ay7<2O{Bc)?y*6Rt6~G@eP0|Mj*>>1Qd"
    "m0JNeVR-Zd{4~Hgc|%Ncr+MwCXh|%eb`<?W0uZRUir`f<YwZc5J{39Tqv}m}h_47_}P1j~L?ci<b=bO{??ufGdjU"
    ";!2q(ouuqWx9Bupg6mZ|o4UqFLC$L0tfTaQpkk=gIWM`i8IE*Ofn#$L1P0KrNRIPl3I^D(Xt5T~smYT@F$JD~jG$"
    "3sB|-sGJS#OE74Vn`isnDaxHeMP2EYXru5uToRdY5DsREAjft};VFv@q27<|b6zCz5p<m?E?jdgvvbyaFagyNh_`"
    "EBM+eFc{!T^CUGv4H*W|JKLC0h`*b<vQhuHEe!RA7j3i8<fFa+e+81q@y^3yTf9&wcRK51NViYF6H`cmlV)5DKS7"
    "FfAB(j@yITE*ZK@0<J4p9Z*A_}mMLuU>u#MJ=X$`@W=67h!uj#<-QQ?_Z{N4m(sbG~H~h7`(;jVk4%eACK8b(--B"
    ")1;!IbVM3_`lGqcCF{dwmwI>I+?w(PQKa(IcN(RCs6I1$oAXF!T-2$jn5w70YY|*vY0Z*+iUFrjkli!^z|d#TJm4"
    "d31|!(F0QgAkPyZuauYsB_y`^8DA|(^cPeCS0EkNJ*!d!(8Sre22pRb4ry$zx8AmRkgZyVIMR?mI>Yp;pyGeE!uX"
    "=9bWGsmqUvpyw=sz^4`N^?x{I1{6(2Vhf;uNErj42xMTN-e3m7$X{&d>-7*><hWNx4va6y(F-G#=XQ3TjLwAju;T"
    "k@#ZlA_-NLnSlR8#3*(H<2sxSS!Iql?1L*&AlgVmR4+K;+_+kGxVttR|=Q3^!pNmwZngkwZXPFG!j`+ttibjG@8J"
    "tjedWs3IpHk0?X~nDPwm~8LI>-X)6XAMxZI#jk`i&jFT$EjrKc>qMT7NqwWLI(5)*jZcZdcG$J!4!{*!=Hr49x0="
    "8imx6(T%D{5+X7uE=CW8uOa*x=~r(ebau1}!G8F1d_y$S4+`OKI4xtuE<=Z=VYYUjs6%M4#v^SX%1|twEdQZqC*C"
    "X6}@VXY*T<jcx=?f<f?*y-X!#OzcTIyPzI(a5UNKi9o1{KFL*LNIo~pGBGR6Q(bLJ$(GySd-W<iIXE4~sKEjdZ_Y"
    "hFEh42n+!|d98|BN+&9Me|1$Cgo6wngaxl-A9$9snZmT?o$`;@?emX7sa^|b2KMJ;r|O9TNp!n~KPqBzNLTL~Sep"
    "Hnyn(+UKgG^Vwez2k3t&#|0Jz=xq8d!QRdNOQi0C9@{%L&Pp1R}IjBGC50Ip$|Tu)6-Yf=N(uKL9oV1D&$Av1V|1"
    "@V*f#xKU#jOFzp}tG%~3~Ewv=9&dN)(>et|4CYQ^?Z`P?Kas$YKYBS65d6f6UbL~TzkGv^i@jJkuB^pxVW~0Es)n"
    "HNQs^dkAu=$_ZH#9Lb?xTu_a{i&Vxzt7qLZUZTo38Mj+Jew(-5p2-F12dL80{H4>eVIpc0x!qi96%Akm4e7#qW<!"
    "e@vco=YW(NXmpNKCLN*#WBj>t`^<Pi7}$-46u)fkfG6jR-ePHWF2{qs4Nd^r-}FRCDmVhH%MK+%w5@Fw;a{@^Ts0"
    "j>$k~pddEZEv@tl7tS6<)oWBgJ{DkJaB|FBNSq9ZUh(*RC)wAD|TPABQ{q}ul1sYxC#vI%tD0%T2iJYbHm3{y8Oc"
    "p$li^dsa=T$c(&LWN)|HKKF$LP7zDkx30MB<sx%3Z8O;f<$5xzt@G%Dv%&EcXS4}i&D{hk5gn&2<dxPVXxwaKP1j"
    "T02tSDE%g7jpg=*Gip!!aNq_*hMb-dP_k<9g0K?`Sy;L7uj+*SJ*BzKRKwaGQd21`z9~Ww?>{NM{3ap1Rs@-TON5"
    "60`+hl6AqcQNEiD-Wg6`fAu5?v@zlEw-lypf;!4nS9{0vwf;F}XP3TvK}<<jFXK2e3q>=swE}`_1YVS$FldgwarJ"
    "%yf*-aBHvYuNL4?1uGoB@LbX%c3=b;s0fv>bKi{3zs;5~XHVKQ05%u5A$3E97(3?cvuZkq2aRcgidjdG;+^WQrq#"
    "#Uk*N6lZ;nxPodFB(XD3iHhUjXjlo(bFotZFBVqPE8m)DqG8P<feo(QQN^<r+pslcBkya6T*-!f-r`;ppvVQkAIh"
    "{rZl1<h%Ck*U`+9J3}IAreN7c%;p;(CBBk%;|iHw_A82JsS9kZFg?OfTf-4^U0=S1#E*0NLSM4qx8nr0~+>ZXxOk"
    "*Ju!xv1nwGPPr{e#>`vj`)C=ojguwK7Kw@datS<bUo6Q<$O7a72{)SQxn;(>Tn7rHH4P_e)t$P>vh(+c)JBf#*;r"
    "^^&_p|r7YI^62#2^WYpuzz!|1-^SOYdg5vZ{loL{!Sgz3NCQVyZ{yJZi4ZQU8U*d$uo6ei6iBgv>K@CZE)86AR;v"
    "_|ms6H{cp^Wt%%i+t66s$tpoo+ji{TBclO$;~<C{tX+Br6yT;ATiFwfo`j66(t7|gP?E|^E<G%q0OABXkxmjJYns"
    "|UcH!Nl<BiX?7+g<!Or)1U%P~Nk9NHM^)+Cm9k4{FfM*F83s+Hm*K&4~My2i`nqo14}K-nlBlcCg<XjYxzjO99uq"
    "iYmYBVCO4p^<*3<#|;TtAR)js50R8ju;5Gn3+m$I0XS}?9oxyc!!p3eCUR}`N0BI)8V{?BaRtwA0fRZ!uy33W%?("
    "N!0K3X4}C$NhnhYMU5P#ol^71Lb>dnsu7|PU4{i$fV;C-dz|wg$&5B*r!?%FdVd&;9g{I#VMmNZIBh!GMLifMy(o"
    "p`0Y@j{SQy0>4<(D6iUX4hj$Zh+ISpj@d>^@rtyG{Ua8I2foH?5|R0q%YTBxT9gUxMQD5<=ki*I>rn{cK#UhZcWI"
    "6RXGI9Fh7|I(Rrv^xppd==G_W@`mY#ZVV#>?bZ7~?j8OxIvF32{_V}^#N74;Pmad&l)~ne^+6)cvkSlBT$aO=(eY"
    "_^aCmwoR$_;fH&97c2Pr-~x!r-hfp<%^Bsdk_?B~5#<}I_%pYkmH|89~YcbaMfkP$Zqj+4wnZ%-qqh&V>$6%B_kn"
    "4(LC!F=6LQ@UO|!${@eb<-5^<ykpfQV*Kb4)C#kQI(VXY140HV$Q4^s9gmleO_MpLDSpWt-BPr=dO8O9%RFTS#fJ"
    "jxcRhWT|b%{GT)waFOY+lt991wvrPQXw_5KPljXn#KSsHZNRc7d61$HWAJlgrLHPRZJ{U>In2`5A@+6IjZIH<?ox"
    "d37^5xMn_Dek6`)Txo)jikDCiJ{Wu>jU~ljon|Z^(ln0H%FFnUNyOz1Igu{wzKOt(6Fh8pRMeW|kFNc?Bu{*A}Fl"
    "Oh~dDsk<DO8fYX*YdyieH5$&`mkJ=ti#gd205br~4IZ)<564#jgUi1|CG7$B8z;%?f$pizhg1n@BlCq?2xnogS?#"
    "}V(xp8kuA+>{S^@!(;0Zw$*k#rz5O!x*#k?gAlN57h7iqUXXz1-qIh`QdClXF$&2WRW=j5O|L%FvFo(nfQq<`GCN"
    "agd{dRYCZ;a8}W3-RrEn2#CrDLlw{hNv`{P5|hIuy^=-kC2&FxZjOCp=nPDKp(wNo@=H@y`*u#0k<5%yb&y)VPn#"
    "3H9?6B9Kz#R$Q&X4kY|uPfVx2~q;c#9G7Om1T8^izs_%eQYu)OAl<S-Wax<s2x!Pmr!kB~+2t!XYbAstcCze$#kL"
    "U|h2!9?OAH4h(Qbv-dPNY}{PZI?*J!ZENL^c=(UROpWjv&CXimn-TZ0P1j-{?gJx&(vxtzA4PRq-R8H@cB5ANd-a"
    "0r1GKQ3CJ4dp(ob8nz}Sz$WR<vZj|Y>tI^;!t&!3IuyVJ#%Ora)ZZ%^BsPq>kF1#SvbdcsifO=fKd1PYqXy7lTJ="
    "xVqsCTGYPu*&!qhAyd4~}1AbZ=G9WASmT2|j}k(m^EC+G+3s(_wHuonEavH<TIT!CQRsuhl}3hmvyq$L>mUVlzAU"
    "v@DB6w>TQXxx}KH-ukI-Leh7;jd{iG>CcK>)~6s3DMGp3l&<~L;FSO<3Rt-5WGKjE2Gi7_cqdhU&B@JDVeV+5$^3"
    "xlffFfCwPT&oA~EmzS}THi*0*f^R}H@W2$XLe}T$2fqQ}j3bOX)pAj7c{FE+9o$#$lrW;)YDx}*iYX}&$<PL9PL>"
    "{R&{QkVv=lE<FEBZmEx7+7_RWHEKE7r+7x0vH_nAG{sExyP+`_F3G@s7S6xEz=Md`+Fl5|I|`1RiE1{<DFCfDNgq"
    "?*g>A!=~-RCqoW4q?dD&q=Bx83CYzWUK-}Xwb*iXOKo=KmXrsq8=aBzf6&=!$Js;joYAR=ZzH1y+ybbDP{<(*#(U"
    "p*f~xfx`lAk?Q9-v}6*>dYn|77EbhC50=?T0Xt%}T!^&m>Q5XE7qReO+f6evncC)tH^)FYW@)U8{{C{RVV)yHZB#"
    "Kj%7McF`0?P9j20PS9~G?u5rFggjbDPmAdSgjj2MnF>$t@}BK8-?eVqH1ftwvy2fT+bV9SD~_#fOaO*E=T2g6DN4"
    "KefS;N-R_FV4&?ZSK4ftXQs|L&4vsc@W@**vXP$o*PP3CK#${ao+QA*WEvNXjx3h+Kk4Oo^*=(*m&m)~3Nkpil+c"
    "?a6u`Xs<&Q#7j4eEZXz$oRFW+N_gOIyEo+WqxF_cUinP%0C+HL(q&^}$%TW0CT2dY-I3@H!d#tf&SSaSfeEeUcL("
    "k(7^ODj+(adhpa~dA-2wKV`n2mC(A}Rag|)f<_NXL(s#E(x)yrW^c+G8-VjF)ZF80Hfv3%!=)a?s|1dW_mSJnh>-"
    "cM`3Z|-{h&xq!DT##U<qI<obp!<qWqzqJlFmBR^JQc5~Oa`JsvS6<XZ4PpdBYNUg-BIn3H<6ys33NcC=hePlo;QZ"
    "O_{7hi9)`_Srq}f3iQmm_Nu5zm;dGjrqFV<7nRGkJdiyCw1hIKE$*?H{1(s27Au!&n!1GcY4-jw#VO+gI%Mj`%ZA"
    "}(3YM%)9*a&bqAQmbu*NsiFFj>993TR>Y6aWxY@GJy;LoIgXBw!%2~8|n7MN3Ku-q4-Vk~l@<v)2)s}FJK5cMoc;"
    "*~k$d!JyCPfoS0p4-=uQ2tE=6QOrU<LR7qHXL)Z|dTI_e%C+fD_E@^4wUQ-sRrSf)0f`_Pa+ME6ff~2*K#+STv<!"
    "_T)*|e10)H&c6Q@W@)~BF*@1LULE{&aGE`jbH&t_B+|spI(Fi7{B!JW`B==VDX5yL98*#gy(}g+fp%h+Orcr_EFj"
    "984ddGP+UDy8=6RmmtUtNu=%vk6{@wP}?#-X>w==AE{*`tGvc>E5*FJxGV?^#TkF;1OqUZmW&fNd7)6=e+B~Ow0H"
    "@P`dJe5*N^uftS=q^UZXkI$yLW#-O(0T*J&$3*h-Yn`g<z{2!bN6dMJ3%QWYBNAP=|1IdLb_?Ms}7)MNMZ`iN{Vd"
    "<X)1Xf3q&zlA^<B$*g3XYz^)+-YVH7D;2lt1;0EYdzNh@KSOK}1`M-Nav&WK#N1({rZ!8)D|Mr1E-AnE<9W^^L+i"
    "Pa_ow@`oXfdo0zqCo>FUdyM2S(R*?ZVFP!^VOf<RJMqHboFE54@FibVT}>C1$^2&DNtXWQaCGSN6?m+aznqS$zqz"
    "a-#!GORdsCm{)qPvleFAc>WUSj#WOVpehcE&<Lv!wm8L&d0egw=*q#J2e@R{SAI~7>`|qVJrGbWXQ=o)(rmqQDm="
    "z?I4&2cmaeeachbgzCM`6o>`|;ms!LA1OBtr!FD;Jgr;1}*t6ONZ?Il~u01FeUvkkB@hrd?05kk3!9Pp-GJd{y>#"
    "~5kB<jjCrY<hH1s7Buc)nM+Q5Z9|G8PsNyu3OCwuUkoHa2g#C)NjFOUL2g99vtqU20hZL<bffvQ{wr)A~@hNymg="
    "584r>v;w1b#y~i}QF+_-vMBP5~HhaVEu+zVgNeG6TG2uZkP^8Vf4MAul>UvV+=8$Tr&>V0N)uxZA8#sxzs%D_dHM"
    "OJi+evXtb2Ra48jC6d)o?tJv_Hi1a4t$Dh#+G`nw@0sD#8QXBAV5|=rOpDN*|&`B^0o*&d`Jzn?y{xsreQ4^wvqG"
    "(BA@EnnA4>bOWc}7PshK!wNF!APFg4P?8OZiv8^L27D`KGSFB=*GE#7KY6OLMF>Q|=`G1_=B2=&ps&M5PM<tD=va"
    "Z+>%?d;UE9KnTa=TPj*dPr;}uw*W%0Vqe!4iPP`pLqfcnhE*@EkxrGHw%59C+*PPbgkbqeiN+ECUDRX)XR#4rUzO"
    "BPp9JP(-R#lQ^S)UXt*HY(e{y+VW!!1(|i0jTK`6rREjIDl$q*j}TgVQDnppk}u^tIUK}x5P`%5fqWYLr`X^Hjg0"
    "v%4>uv!WLDFY`(cZ!`AUiSHz>T#tL^%dgL-CoR`@FM<iIzY$2W8RFwAv-wr`@YV4qm1%wM~tZ5;KjOt#TLG8cMV@"
    "rP@pHery`sugNzWqPFXaCqU|E>QrGo$u+<$8e3Kr7cXgY{(L`q$Inl<@)&OYvKuArs5ZI(}HNyN%BZ;SM#cg(o&}"
    "*udG!w-1s)KK!FL59D+}g|Dz$T%C2OVB%X>^M)rFCO0oJ+hlm(1SMYH{i8RBr=4%Q+1^QZE){&JJ*Sh0Xw7j};_v"
    "}A*T@w^iRbGM$LI6x$^YjU=RWB+f=+j!Nhb_>*SEYMHqpC3N@Gcyth^`HeBH5YV|MZ!xAC8|X9>MY?*>5ebzmm32"
    "-cTr2^*H_-(Pw9#V{JHFoC%yFc`V9P>v6NHue|p%ju7!?A7SS52Irr1A|aU>JMIXKr^Py%ncYqT4?x+1QbCtyhR("
    "TMN0_+=dyk#^>(KK&)vOPh)}i7spD*h$Tox)FFWd676vqC1nlT|>w>TEsd5M3)KkR9$cj}1p;q<lm@bM)<<+8~ev"
    "-BiJ$qst>O#HPtiV&CbS`XrTt{UuP=x*oh4pN6J+Cd0h=aHO*OQ||6qM^5?4o4!5HnMDMrk2Ns1DHL4m5a}jDvy0"
    "(b35PYRj}*3%ChuUd0UVhIp~Y8<9YP>I-LB40c3v+44xsQ>P;a5Gb2DU5T=l)Fvsy<N(EoIS{d#&soV>TSlEL=F}"
    "&8y;#iJCE6Fb_oBoVZV!QkDh)MSBwS!r1mbS1YmYs2539Prz_NR3kcA0^)&%(MPuBeQqyt{J?vuNwXx^SOTBEMz2"
    "<ZjA>pUc!3ZUb@X1Pw;ie2C_2x$w(XLKizsK4-hV}xDNV&vU_hj@C>a!oq2+}UP=HLY{CCMb$e2o<pfyy4xW(<B$"
    "Lho7=^aeTCv=8O$k)fqFtud`ugZ*{*tQ)|wr%v)@E+E-g;EF}EwKk_bDtIZdfr$3=zpS-{On^^R=o<2LQ_UV-dER"
    "~}u-H`Y(;lek)|1UP%fL-L${}luveOz)6A15|ktmn(u^kwzQYsW~vg6_M{HdO&%I;i%eN-@KqDl;z-gS88>3^MdH"
    "!vl^kenEB9xfiV_l8lUz$Hvy`squ*%5fVkbH+E2C4qHseAi>E<h#pyW(18;iw_*cJvnn18y?nOc2P+vK?(!599xg"
    "XkeMR97o*m}sp{LL=W`fP<wWI7kQgS6H*=v-xG<QKS$$s{)o9QL`B{t_*T-3`A<($JCK(DMRPn~<ug5L80CHEA)`"
    "k5IRJyg;(yjrUct_0Ve<6$Qp_sz0JBT>O7De-e(b?iR)6@kl*y&C-l&<wF}>Da8yQz|H|@y{ewzd1hsT|F~y=sDL"
    "!LOOC^)8!z645IFU70amY97A7P&?M2P&IlW>;?^<|7BB$Jij<ym?FitEPWt_)6SDx9xNrnTTb$KKZ3PfiK+Of3j="
    ">wTnWkzuUe@Oj@(Li4c!j4G;FT@FU$sbr<br-`o{gAiu;HM>J0%!dc^%;Pl20IoIF1zLI%Zse23^c=ZwTrWA!Vtt"
    "Z9lBGGH*LXw9xT?EGo=@F|*J0R>a0OECt-zuZ;C(9@XhS9D7UZzfq3LxdV6t`}{jRxx%tJ11W23Yy`MlUfNPc*iV"
    "Fa3Q}298lAqpwFl9=NA^}Nj)0l8z-)oWK?~ZP@0yge!0swSoiFQf!i`8<N!wFFc&<PM?9Ff6&^nd93BP;hrZ(Z&*"
    "t8msvnu;(tVIj5bWimeIEgX+KnAd3X?RIMP7KJ{*I*nDq$6B=xjKO!BZwL5%jWyT6zWu>wP%;b@nU>2t((#-zW;*"
    "rM2ieM5hIqg+W?>GiLD@ZzmY<EZv~2OI68yKv4uiz!+zTZsf1Bc8<II$4fK;a_bi)^!EPy%f@(^2;R75<_J>)Q)8"
    "jXz?D*h^A5Ww7O*gp19VDlIfmx)m^42s4?;6CSNFG&d=kC)W2HNi@ZoH+WzmQnNP!0v}`q_aw*$|cm;WN;4d)^0i"
    "b!v#5az#@f$DGBrhqkLgcE5AOecRVKe3CU!z8TTK)#ZQR&yGjE(Z7%O-<*z4_zoXF!ty1*@tGUrAJijJZJYXD&eW"
    "heMT*FY6@X1^<QJ6H3Xl<_TDHr)n#BKBlc1=#KM|;bMWE}c(J)pO>5?4oCUjqK4yrea(K|Zi=VFjGJe9BuU6064*"
    "5xw$dr^VmAS0Dr14{p@?%NVh4xSbpaN;rRM{N2cn1<A+Q7RC$m@ek)(pTW>4<bZ3J@^vOF?lSn7k=M^#f8#_`ewq"
    "=7o%RFYE97gUe+XLM!A!7U3>_A+|(=M!ZsY1ZUO*UT(_y%%mI9$4#gK*fjZ<m3)Deh+#jUl9=O53D`v325T5Vf&M"
    ")QVj{<6SoKUqB7AUX`wx1IDnN99TS#xndqL#>BfUDvo052I5vxekXvHth5dJ<{RCYF*#xxGB0f>NT}P8#%2AOgMc"
    "idoL?z1I_Qr;H5>2h$jzjs8|8q_%SKujDy_=7|;>dYAQ@QwThb(Q@yVk@6T84OkYV7!HlP1HsJ~XN&1ACJ}JMKO("
    "xbl8Py&*ngyHAeWo^lm~2DuopB>V6OoBPx+?dgp*6CL8(s|N2g*ud7G$Zv3SI7Hbb<uBT)QqU@cRHACI}aA-pT}a"
    "4)GuB)ck$+4}01O}n)U06}MZ@`a$~1xdY%Rf~`xhBcK^u{y|Fp?v~upae|9PIy1=HWj)g#B(T-1};d9_M9W2=RW8"
    "HzeeBKde?QQE41sE)B3dSM!&yHb)WoHFa&0otUb3wbzKg!&rkB~Ngw?I?n&Ldc5YyH(?M>flwNGCW7J&%c`a<Of^"
    "^~mHR7R&Aa?Mi1Ea8D?^7|>3au=TS#~xeqB7l}Gz(H#ww{?|3FX1@bMB|tqhs<OmNP&QgJyNb`IYh;=~7Vb6k}X5"
    "KQ&f7;j|>!b77K9^3|P3AG?-p#@6f+ggsSXp$<jq>d+wu<p4EtfOIU*4%52tV^B`bV{AVr2n1uRL9cdeRpL`hKU<"
    "F4Ix&=+b*G>iiNbgP=<xLT;QKd_3Y{HedXm0bB`OIQ#1ti48CUl}{NZ;5u&&B*L8H}!VOBkwKenz8w_JeR3(u28x"
    "rgq&K+W@N?XAn%Lb?w&z{hbf8p*133t$@}`JDmCP2SIb;p$zuD-Q}B!^D5XSIiy&(>z~61YVCvg#&;w4>~pa#Sm@"
    "TXw_irsH$RiX<t<6IX4;$2w}>m&@XJH{-592WCFHRq~Et>bfVURu1ZcWM3oDJz17+y`H@v5%pmRnnFTsHJ;{!KIV"
    "9tikE!p9$A|k8N7f%@SkD@{uR)hsY-(euW3Nq@(uy*wHg-jgc=x4$fK(j^x28xHUYG+mEdx0I5E3xZ)_#-paSxyK"
    "D>-SKi-OzyJhZExSJoYP(zX%q@m8{JzpB%y5u$Ue<H&&#hWR|H@JdL*?iF8*ULE{AI)?tDF75^1vV}R?FEI!a4pY"
    "rPnnPM$N-1#ZxvdXQs5KFsg+U-5(4&xyIzVTzTT7+nGLTkt1qW79CbL(epIV7@m=VNU)0!|~Io~)Pt1R_~loU$To"
    "3E?+CVCTS0#&JUhQ*3<nfm?y1f364Dw!qFuybzSg>VO_$43Baei{x5CM^&q^xF2AvO3h5p=ch1PjC)#+rl#HmPy{"
    "$?7Eni;kAaboo@{LvAr}ozQ8^hP^K1MC9}XjS*yAw(f=X4K=l>$h=((ZkxL7*lelw&&9IHnO*6P_48E9gIr$w}rs"
    "hShUTZ$?&SVpn6AvYYo1Mg>#y!pPA16qlqv=fvee@PH7lkD8F47a+<9Mb>X=onSsh2=d7_OrTGRf^wML?1&Wb)0!"
    "RxZZ@d|_Xem%doIwr%Thkud@=T`iW})P~zAvJTT8xnkz&)M9c{+YU;eE+CF<zmHQ?q4?NqtaHW)1=v~*LKj?LZ(G"
    "fJPQ|Fl)WVv#to5?f!?s|83_G%3m5xYy5V2Oj36@<(+pr3WkShI2kJ4Ze8Y_X*aLd`Pr{J@7VWj9Jg-<X6r5@@~&"
    "Tf4)1-7bc^4;hWJ!A#d)ERxiMPsdqG;Iwm26SgnNyBctcM2Zt>CVa$<lo+>;Z;&siUw&GOb=I^)}-rLfcdr<wsx|"
    "Ce-qV7r*=WucyW;g(Qal8F38~nRe$|XQDWZireT@2m!6OhEo_jq5ElhbM0i6yX3oB)C$|+qsG?%9-*)M8B*n$j=3"
    "*Rl(r74f2oltNAGxg3*VW~jM{=`V@vC{$ZI!gDR)BNpP`gwC8RouTSwYc4r?x?(ZbZq5CysFtE(6A<*bDJB1>KLJ"
    "w->Hgr1ao)cEs*0)eXHLEleKv0L)xpw85)ep6xklE&C>?*jX9C;UF?TMPRxU*>d#D1dbJ|ygR1~OQ8w!5@Fk0Ro="
    "@8__+RQU+<d0BB6AX-qna6+X2J5T?|9V*c6%c>|$%}VweQpX$mcUm6me~mq$Bvc4z2DF=lQkkV&Gx0Qdb)J2AMDZ"
    "(-q}(o87{5|wZ^eHHhp?fvIwNlnj7?W%EIH(Qfe;iB<_ivzztlNScR9c1MTE4!^<->$$z;+=dfIT*il$TJbJD^iV"
    "_4gWxQg;i;7CE3>q<27>BGOa0eeaAX&VA`*ao$X0~PC#g}{qMO!Bd|3MUMApLk@L4&^TCg846O6DCmYxuE;SWLiC"
    "qUV623m@AO9GBt2gW)@V)4AdBTObvH%qgWEFa^FeA`hm(YN1g+w9^?mc3b=!B>Tt014%D0iCFs@in}=fG$&vmW;?"
    "IiH;Q7NmjzwTQ6<G+v{NQGKyk-K$Y59TUjJ+NL=GExk6oe_kyMsj=TtIj|}clVn7z{p>|KGo}=ofN0WDX`CL(Zll"
    "XB5~O`$<C^?EUC`39Xa5petH2c>V9z+mlStKfQ-K<-$ahmD408r_VHdijyiq{`9ho&gu&`Z~>#J%Ro@O!`<!)eM{"
    "V+R;#DM~;{~Wf6Y(muuj@rY_6N??POS{xWhtx*Sc;|IA{SsIu-Ss93j-7%+k=NN#uI_3)C2&uZhEt=g{k*Mr=^Z4"
    "|q)6jI`r#G>$dcwYn=JJXMgv4mcvNu76a2^;bayTki8C^u)H|z<q{49sp7aUwKve<?8ghh&F+G`=WDbH0<GfaIDc"
    "AI*N3~@#*p!b_{(S3^<BfhZXka4g0j(3dTIZ~{)2QBv#g=B$_pYHMJ*|o7qCd9@VYXEtI=iLxlR*YZDQ_`b8Bu2U"
    "=C|(wTH^EFuE1q7RKG6Q)AFL&%+?)ucwF;@_uV{u`@Y*JFc(%KqD;vtc6VSXXok7a5YRj4)daIV2ZIqL4DdHQWk6"
    "MPZ0qg&wBy9x`*5Y@aN(y42bsrDKFc)jo@|eU1~&_Oi%YRJ5{z1rLvQcR{Hr?XqDJD}@Z82Bc5>O7)q*f2^iMOCr"
    "6^2o6a#Z`)vYwdAWic5`{Y*9uwM{?(tD&g#a4}S^<~?VzQn92m1pm7P61ZDndP-u3DBRjs_QL&vU_ioq$O>Pg|?a"
    "@J`z6|d6i@+rPGoUTlTooJW94QRK=lGX6NZ#_pzef(t#n=&?1ord|j@3F5V@|Aq2tZW=GE{_!Fc~u^S34z<{-3j?"
    "s{*Dk3<)5x9rU5ih2U)zF|WI0bw>JgX{3ax>?kc@By8bMaSvY;baehMDbfa<-lxDHYMB5W8f41bPgW0x;eNL@=yk"
    "gpM(GX0&C0Jm@TWek_fYA|Bjr86k<&MD<5WdI)HN7R@6Ctyc>r@Lb;74oqHe6#pq{=804KEqEuUa}~34TNr@Syu?"
    "XN8YWSSR%AK1MEohuQ2>b;0{bObIVyODMFG142P9_xe_iQF1(|+%Nvf=9Czk6eMWQ(Y8Q@mE?LB{Q?GsO#`jVciQ"
    "V-Bg!s`rGiCO3V%_i*&o!t(V8>h9Kq_+r7<2CngRM=<t>)c2U=T)Y>T~?j`y=(LNhxLOzI?j$quV3x$kEoTE+X>I"
    "YB?;+wn`&sxsBcp>Qc?S-Eo}h5pbwI-vN!fQdK7gsvJHha<z&#|*14xVV!3N`2!q$l*pq8fIXu8nPzDCrJrY3<xu"
    "rBbqyfJ$YI-jK3AxVqys6`&QXT(tg{7;_OgaqxWdnJ946@;37gA#?)ncmbl&Uqy>xDuH!#wDLKGWcd^vlxJP+RKK"
    "%;l<k^sMws(g+d~O1ANjxM{8JO>C}=E2QOphw?}8yDY%aMsWhtw69^C)9E+MBSPlI8oEEj7P-I}hg20lO%Uw%2C`"
    "qsgcxKK`z+$0$b$IKT{)0<WNkr<4BmGy=MJBJ*j+a!b^1|LI(?I<o8}~ZN8Z)^Z1G7j?Rb}hem6fEYtIN>jels%u"
    "xEwYNjn6-hm7JO8Q92mGt44BD?qmKp1C`UpvIMlCvO1_3^c!B4)+8)Ncd?Y9q%De=xYb;P_3XF{k?}B(b^piSDdv"
    "Cy~c%x#v`bEEq93=^=JWbRB`j*==_l_t%D%LW{v@95WrK471nD(&Bz?|SFQ^(t!qvS3%6k}9eJvQtbfP6g%88g+~"
    "FeF$t_DswCI+RMtk5AVg}HI7t1SHjaR0fLgN)ua7C^7n66jCmZkC_Ki!J?$g*FJ_T04YzoK+61w3~pJomiqv{!sA"
    "(`R`g^qXV4cO&%IUs>NyOFNix9x0c7(j&RM#=tk9wCJN?c&O{SQ4(wD9pVIr+HbLja^O|=;MZL@8Cb2EEiT`_UT|"
    "pwp1`eH%ds9PBK|#>G++$M;o~<IzPCO2JMEY^;X8lLQ?^T5bO&qMV)QhEQRL024&JN)GU$QRA`p((o3mMUZk|?Lb"
    "I~G0SvzEVh%L^Fnz8f9BZmkiwopELR~PyOHxy<bEEGNs1GiCxa#C-M;rOwtjj^=6ojj>MSl9)Iau7mIA*l%5_F`J"
    "xVwy&IiLnrV3c?mISJg)kxcI7^Ep0wsHSf_&QIi3D0QWh7Qr}w85LXzO-~u8anpwST1^MFFg4|^0eOaugGw9HaNG"
    "_1ZDN|lmmzRJmQnfX1YUQAj`i}B$ye>bjcWyVd6CTR_aYl>*gQ3H>kbvYE{+;c3%FNGwURUc`d1rL!V30oGQqQLV"
    "VxPHG>d%gU^51~pcn27i0W3$VPmfu&M^tf-k1*F5Uh=43oj<h>%rQDJpDq{XP}~}FG(6#v92AJ&iG@tSLokuvbpf"
    "4F*fT<<(H5TV-5h=K<MG7?I_`|eKq-WNYE&6Yw6RwOljxVL6%^g^9jqZWT#H=LUK=#M@?DpCc8o3wfi{8XAH6x<K"
    "l*7jK0V$$JUKW$I66Gxn74l?pzZ5#C<sn#?YT!^A0NFwIvKqfWS;}K>FL4GqrjKCzjwHAY{M7gh)Ucs(1}Fe?>~="
    "@4_^LyaQH*saKZPlj`sgNdeQXr%e{kF&A-aj`1j-t?F^bHDc<6|@poL72Tjp`zvK-0l6!4No|*%Uj;T<_KuHjbkQ"
    "5P$e9}Z>@pN7s@4Y-V6S7|%kM>^t>ZnpZ(7O*W)A#M2oE-dc2=ldH$%<?pOz!pO@#gRlsObU2@vZ(_{d_R`<w1kt"
    "o!*-Y5xI-@f82vg+wt+}-`<Q)PInnMx+S%kcAt-rUX8|kZ%%(aIzBl4mA9GrhjiXhy9+;<qknL?fAD(m6&#00MnD"
    "<nDDs7jGQsD9zb^sAY+QcAtO(HCoUc@-j-&pxXXbj0LoR0pUq|X1o1pV`dAUM0n=mHPFUsz>V6datqvO5PBN`55K"
    "HY<=z}O=2%3S7xLBj(Biwy=mdA)ah%p5=s$ViAy?}UuwfZr;94mM79UVFPI@8+cWh5lynG!K}$leV7J{Q%~Qv=%N"
    "$_V@TL4CA@>S`2h4i5UVYCZINahP&@FsIR_8xSG%OtV9*@&DE_@*7vMLHEI?T19kr*w>d_`Zz&f97Gg#H!T`cHmF"
    "LSH(1-WRD4rWlV+@s)Mx+k`x@WPdOM)kddv31aBTNT+j?FgHk`aUH#r#Qh-Ts8ZL=I~X0$FTcWoaHT^}p91K>ULD"
    "Lx7QoSwdn{o)$eOr>;j`yXEp6*>oQ10sAbjK+YY96iLcB_{`6~12z1!Jg{-+WgOI^$c<x^xErH5_Ym5Xc!KRU#+c"
    "L)GA`@;Y<)xaV6g3PV9ztKBW6mI%MciMhV>NW<PW!7X_)fHF%5us!|uNml5X$iJ91m{hiK0Oq5C`SH{!;B;a+1`0"
    "N!Y>t7nvX>K@8W>_0Idj9M9f?F}ZK7@{w>o++m!UlbG;8h=v@>csx5gZpjwRw&0dz+0a~doYrXB_TU)AtjA)<q>3"
    "d#CWn`l~UGoOA!d|<lzGCz@EI{Kr)bnk`NY8UiV}Qh_>u(0(y@yN9>kA)tvzQ)3a^69?JoIKPi=kB$P7%#ghsWup"
    "*bmYLz<b_EbAJ_jPe=G>kdn!45*ZE3vPXYQksobJU#JXt$`ug+H)ndG~<htGwqGw%|hJnGbX_>y_CvoKFtf(m6rq"
    "OEvLx%)D3d!+_TTHL>%Liw~*l#4kO)HZn2?Qgg3_6RS5+ESa6n7MK7ZWwx~$`m9&fPsihGUaiMt-{=>$V^v-n-C="
    "dx&-OQ~da<HxRg5UGAE}rYOYAa$Z9w5H?avCMEg%8!8}s~A=oR=9d*9Bxe}>3AbkBhile1ZM2@0c3ed_?{G)*3YC"
    "cXR3@M88}_^|t}ypVh^e%kqF08T9`AdsbD1(*a%;~beE_73*#_dAaWNpPsK@<1p2*$wb+{`&an=Ytoc;}cyFkXm$"
    "Q6B&x<k-)(mj%qU?-aVpyfQ$S+(3ijh;}v?P^#!<!c!jr~>XOB5R$LcwNz+o{#mdq!YQ|XBsRJ!ToX|?WJM$>3u@"
    "5u5Y^bro2%erom&MV+T{+yFIW?TKLw$xvG+P{^*`FcO69_$fys;w+V`swm=vK?-)%geb;XZ85sI6<*iS1gakVl>o"
    "1>{&~_bJb4Gf_#QP1~Z4Fqv*=b=ag<vpKzuJ-dv8RM5}%h_}^d`haBv;7j$Dxnp=rIJ)<9cJj9vrjZYe+WrZkYW!"
    "z?wOLm)_i=M(CWrM6^eE`Ki`=)gY}0;~Q{xA|68!tK>P)VBZ9eiZ>)RzJzq99bew$~8lGls##q7SE8vge$b^;x9>"
    "wlJWTqCnrBqhwyXXVJRfn#zQWb4gxRuWU`_xtP-FF#d4F;jEuDnnQQg{Opms@GGaCgEw!hM9{XnD5OD<L`0W^fe7"
    "*ex=dq_kRJEwp^`mU2MSy6%sK7raW-<Q)mFEbNBAu+<rDsynFYk52nYe)7^E2ko@+GWpP%`j2UJNii(d#HN(o4>}"
    ";{%UPO#*6u&Jfbw)$Om4nO8k1qk4UjKSAD=w1@!nLX;R@SEOC#|FTm+=mFk888-XNym%E6nYib2vtjqX{6z$%~rr"
    "cYUPLtChNB1Bqkp_gdiE)MaMn&x`?-`pH&#GEIAAPt<L0kZi9hIPRwSrbR7V8Byp~$~iE~C*_hKlT9}WUT47Po&#"
    "V@I6Lkeaw_4&Ws}ImmLMc}u76P*J<t^~LByl%wCncb=G~V|cAx^ew2>O(v0AA@#D}>Gi?zha{h|#$F;Z5T!0Pg&D"
    "tu%XdNb8qS<XLd4UG#VQ66--_;P%KO2F+9F1sIR8hvybQZ|W#U!MAO>xV<BC@*Ajqb|KJW@Lq@7I6)=Zga4%6NjG"
    "qDcT!ToU485)!}#ZG&H``BFWaoieE?MrsRlNT~Q<%WP%d^4i6cGuj!R3Lqj;c>Ie=j#EGJ$m;lD2?>XC4v+209WF"
    "$Shm_5WCgOys3?7~5p#i}k<9!ZV?Yo`-?WWq~t2O*7mwpe@^Z<d{4MMTERO`d{Bx=<gJ3Dk|sFL71WD9}0}wAs~U"
    "1sskIYwC}>D*JU=tjv%rBgZ>``lr8p`|jOM?|t{P`GtD#bzqF{UFT2o6T~Or5nZWQa|asTBjjlun?qQw7L=d#4Uj"
    "_ZCgPvXf!HSSzx~DXHe(0ya#o#JkS3y>z*ar|Sgf!Ib?xf&&DKzHnbQKK^*GVuqVDsw-oh8}F>L_5AXany7t3ko3"
    "wO1$hRl)xgAVsD&%QC7srJaANz((-=WgdaSr*QK^w8TI6N$5$<f??xMDOc8y(0z(|C>9datOEQq!}7}#68QUTG|X"
    "$V;^}B!rlr)rIq)=73SMJZ+WKtlJE0G6Nw=*x9}HQ<}t}>WW>Q0K!VBdtLxI-HGKXotWQ9bC45*{m=ih%J4YuYSc"
    "_c0)+voR`m_X`)h?i|kt+RlmK`e9@UO0K()oj_mK?#b?iV*cH@2XW;2U)n>FII_ee!=cvr#{rPyBN?4nJZ=sqDJh"
    "G;;z{tT}hwKFxXgf^Ya=tn{7}>*BB2*4AHXYg)cfI9&;yU|IK_0kNBx0Zbd7$(=Aes8K`|px7Ir{Du3k4k)ArX-q"
    "39-*!if+h7`1>VuKNnV^H6C*xWV@+?GWX<c4|7)O8((#|$>yBI02LUkc~)lVpNggS&cYjjPZ1wUYQ5%3+rRtnKx0"
    "L<rx+cB_@7h?RW;$i4Ts_sJXKDjE+N(ZYrt&BWF{FNp@PBbi_I7k!3LOar_dEerKW|o9=P^-@7-ijRsNiPnAID3d"
    "muwP*GgY5wxyH2>?&NRu1!rd3Tv<ecC+4x|?CpntEhzGNu{jun6k|WShd^>%J=D`LI3y`LX_-2rskpF!!I2lCgA?"
    "Y_6h(7tZTLXu3LUEX&Rv{QPFt1_}R`;7P@gI)*cyi|W3(p(>Zkn|<%kDLEdsqAHQ<up^?mV77K39C-FWpDQN>r{q"
    ">)c?vM^3N=hI1pt9vuYTsfjMLOoy(fQQup3m3sQXe{_xhAxN&FEYQ>~-3Rb44yF;ff<4K0)Y}26pY>gea{&xWc0Q"
    "v#fI=Lt*VI75==7^;4{_Hva|XQvKq{k=*BGlT4ZB}g=k=~EZ8s_5rryM}L=7Ng2wb^iu!1@}m_pXSRV|mK=$d=__"
    "_@>dWVT!r>sii@^_5b#zs;a9r9S*!cVrk})58n?_2lUAMG5OWYE<al8+77M5oWQhAs=l4&t~}f-6K#|vHpYS64qR"
    "=ikqSQ7W`z#50zbiv8oz16HpcTxjC9y-QVt|J{GeL@+|)DE4~!A%b=FcJUEx0t#6l5Mh(R8{{VOJ4@N{4H`Z)PzB"
    "Ilj6@SPJ*;Uii-YIlUaT_n9!m(e7(}6B12fLqXr8uK{NU&a^$4l1hL5Tu+I{ped<ms3)(?^rS?mJ8P%N7g3+lJiB"
    "aMB)w+!_?{&iqLn9J!dvXdvg}dh<9@9{O-WW`KF1y;y#rRe7yYP)I;F^j;-?Z17@vK3>RiDuG!u5Tbio@CRs-zIS"
    "-~<MGk!gZ=T|>x1#1N56W9(EI((>5t>nqd$)hgG=^b?Y((18t)&O{~RT*>fYD2=2dfwYl3>@IR8XbiKl-8^|&2tg"
    "^*$1^<c@-+`!qHB@)L=@K6xvy&hleRm;L*+U;(*(z{gwn0CB*<Z9Gz*oo3y4f3_q0o?`l9Q>nF@P`1_X1?oNOC9h"
    "rpLKIwwp9N~?PI&gvc`3^!9pj%L}Zdf`6F>n5ULr{B#F&nvZT?Ap7?z&`>bws@6bPiDT(vmf0nC78}y>ID;fH9!0"
    "rlB7y9+myf9Ytbi$nnk!x;u`_)GwtV-1+0_dMVIzYW;SSVa6537AZ&X)$ohNW3yq%3^M?jy<dso|W?lP+7{fesuE"
    "B>ZN)&O`q9?X&lc-iG_YZxpKo*5Dkf1yw|wydEx6*GE7iY<CWumWhnm9;grnEEn1aV&(Rz02I!hyDdCAV45}#FBW"
    "b$o|tccHjV&O=+);}C8XMf!vr?rFmYNN>BE8`_Q)w9uTF`LqbZ<C+km^b1i?{@cOQbejW5K%$1l^yHM(Ct7^A$P#"
    "y+*p*-?Ncz<50Gq`osxn#ZA%N(SE0N&Ck1A5NkZQPQ6Eb3iV{Oe=|;kAz_i+a*9!gOZ6qp>tEh@%M#S;Hi5?tle*"
    "_t8~Yz39^@8MP2E7ARwYJb^^1$Q`Cvcilt^Mv{6l?x34Z;^Ja;X>7k1nFRb#X2~T?vd<9QlTE)=<Lw_Ay5_|xjWn"
    "7QO-V)*%D6aw6lXB-}S#f#<4_Z#;%(J8Kue_x9b1Vd#0HOXE`!Uqu5^k$T$&!#AvA<mlk;MI$6XqVcj|MwwcM}E_"
    "1aB$T&To@EJ`ef(`)=}iO`dw?jotQak$idEpznh{vS8Kjmh0s@)=+$2-ifC&g#UyadNUo$z;+=+88kPyrozqy+tz"
    "4!b(>_>gJS&Jd?2eX<sI|4j;>_Zl2P9{DCf4xAxV`VFG_j6=x+Y(F4)DJ;yX?JEE0SbeV_Zuy93?R(Z%fAR@cqp?"
    "9HIuXDqh_)PRizK9slJL55x?ltboo&L0W<_p;P(V&wtDi!i69dl%{6>N@tVb9zgpa%*^Z^}87PX4<r}Lyn5fJXPN"
    "&>UfDaJPDiO6EHV*Pq5^hGubVCo<;h$esRd|2==$C$7q_xa46zpwaG*=-)5?L_lSqMzaJ4DY-#tQc-vx+A<?k;D~"
    "k8iiVfwDykY5v_OI{?OSMBq+df6OA96bF*7nLHX!gr;7*g_mt4=W0+xHw|MaA#wGfZSrbF05U+=>r#E9&Zu$g4;-"
    "9BHSb{_QLH6d!^A@86Xd@o&NH2iNR!H+&-9D&YX+i2c2Wak|reeTr_%x%cD;co^RfzJ33Pm+^P;GUBcw_Z_Mo47`"
    "lIoqU<z+~~sp9$vh}m<fNJeRt>Xid{qOW%FLzk)+XLp0V>vP7Wmi*ab@tH%`n(-?Mc-k_ystyG<mC9Dw1i!8$bF7"
    "`puKJ;1hO6CRnw+4T28&Js%<q+rRjVx=NFNXgC^4ciMGCvo~?Pj={y{Hr+)+b!uqq(3*NPg#vz8Q!Y=<6*5MWS@A"
    "80(V`rZ;lfaF*BMrnfz{$oQREMY8a1-|CdYfD-nhsKgXCI%vsxpZz7?VTdZ>lZ(UHMk~r6{`KkAFD<#1BQ(H*KFT"
    "H_WZu47gACKL(#J?E6fr=uJVBM>w*Y+j3b<jHwNdEt|9pvN8)=DSkdW>BCzCcT!(9|8w_!9(?xH{za+wb}<V;5vp"
    "G>0zS&fhb9VJ+1M2QPN#w`pJSc7HIDDl6%!pRCrN`mvXG11ong2(*T&Zm~IN<aW<-n&(7bTdOtXIw7>jX{_(RWX%"
    ")4-SDnIyup79-r)5W;M%2}!S<Iwe8CufgLF@`FJO@_XC<}n$@n`mR^L6kOS_4kJ2@Od`;1dswD~!FzC0^;F5J68?"
    "4|vG)y3-w*57CQ{qN)8MGz0)!%M(7dsxlmIeJG39aPO(iz7@D>F+2tklapmRZTC;Kaxa$2XC&2q!YPw8F44+&&4J"
    "Cs{Y(J$0tX}e`5~aKk_*L$m9GYkMoZ_&aaopnJ8;(97DlD@9fkKhQOZ6&CcZ1IsTi-s-$}64(mfk6Y93ODd^&RdM"
    "H9o>%oqSuaykw-u1s*LSXCq1`a>>5`T?!z)19mIe*DCzmTnbampUMIrIUKNhSrFw8fd@;m>0;>(JlP{UiVH50B3u"
    "`G0@p|NW8w_dh-VFTyeQJVk`i+tVn=3U|#xVReoW9~Pj@8M&>CXk%~Yv+6@BVD^k3V;`PV9}8eSMqBzoP`LB#$J5"
    "i-+2rZR=TFbCiuF_WL4pHm@@{U}{L+|&MzJgqgld-YqfysbsTm+{Z85*i;+LRn-_1K8U%mP%&tCnMovb(0YLWA`9"
    "Iov4jVc8`Fhm_M>TEJ09NftyJ1ftN4Yh25S-hL`G`L3`Sf%EP^NZ?I=7S4zTo%*XYD?yR?P0NiVgtCeXC8NQ^z-O"
    "=bnwIBc<+bN;px~+cl`a{$!PrM_?4N&yUn-Hp8tb9z+8W|UM~kvpW>9R7DoMk{`?>Q{vXUzPA2{45q~;*F-i{imz"
    "#3__vVL=xxL>XkN$nM|K{}Q*xq0Wuc*5%BeS2#jlIAoJ7(9;%3@WnzRS*L#ry*@SG}9KR<D3`s9BznOpc37pvbt0"
    "-*6Lz`Wv8}$z%^yz+>!?Gnsq`SHGKU#D2p$deTi5THs~HWdTP|_Xa#G&2&H^zBS}IzeKpJ3OYi}zcSEpeOuoj9k|"
    "hn3VT1s&LMcIO{Asn5{7!u089-%F8I}MjojRN{?GBp#!gn$t$-j$hd&=2A07T=2sDB_c1i&B9BDpy)<j5OhKFOzH"
    "U3H3a<Q(#H!t#H^m6abt5Z82l#q=FAIMeiz=z@Gc(CE8@y~m&4ql8;PWMjVoFMkoqabR;O%3RSiXM$memyxI{WN}"
    "keDu@nQ@wV-E;g9lQ)DMXD{KJ+xN`wE8a3j`;7V@PhrW#OvRm^F0cX*vgCi<}-<XJKOJL#(_t7xduQI@1hueW&Lj"
    "n=@jy*bj^($a`nbTu9KH#hvgA}@1LO25$3b~<h<R^<2VxDIgAl8gr!V$RVCN{^CCJ}?oTcH0^>+@f3dGhQD4~&3k"
    "*rf#ucGu?8@n()CRD<lFuwxjtl$vj5vwzMrb-A?S8f0((37nMk%YOzU)kB+gC~2hn3i%0LcGu5dVwWmNODX47eMM"
    "b(d1zpi@?@S<_LmKy_^fYbaEPfEYoqU$%Q~Y=3hZ@JoPn>vynwlNu>#SL()c@SjM~CzvF)`7-&ZeYAImYx$POAc>"
    "O7{QIgd&0>j0-2Z&tIML_wYv%W4eDx=TS)fSrm#c*vZ{uZ9X_lXccDXFm%MV7I>_FY>!bPpy?fGRiY6c6tyq1f?v"
    "4KYW)vL!ROf;qd?q!J%|%SPi?LJ3Y|xCEOk_X4TZ%A&g#0Gl*pLYH0*8cuKZ~uM{?MYy2t@01uB`JvREdVN+{hIs"
    "?W-gg!F2b#_sJu$==m-v#1I8J<)aJ(j#opdOO*(wrwfp2GG6_)x=vu=B4us+;+W2AF}eNXl<^3n0nZ0ES{a)Duwk"
    "^YwOfOo`v#dHc=0{s>G4&%Mk3CHoBXxO;H6clyTw0U>cw=ogP6o_;g`_0FEAw<!mwP<%QU?7HEHdvvKuj-Y*f<hA"
    "VPsqAg-TniJ@{vU9fNh6cA&rAf@7>v@6lOPPfj3h7Z)kqr2FUFuZ`%*JzypKF><T=9y53-Bd0+>S3=;CZKy(PsA9"
    "|7W?kG1)RhsH1YZ|7%*Zz;3`^1Qr8<;$EL`2HC?madFF3Ql}{!2SZ^O?#*4<^fd)60&&*o|4!4&h_x*x75*69PF)"
    "as!6KAyGMxY{_fHDX!B*C`OZ7X*^S9EM`0Y;DC*z<UqNmXc?CcKK?&gybI_-o>t)@6RqGlV23lRGo6FRO{I6a0A^"
    "+=1M5-ykDfLP5gW&qN&z?oNvJBST;msk}g_vBT4f=8x4x7RTv=71=o25IyT2$w-rSIQ9d;iw%F?<Hq6L*MGDlJ8p"
    "pRi31(JU#s4uU;^JBMxn76GwX8MUxPCmUSfzo;;t@EJmd^v#ODy0foAJ>-nGIUHua=jbsu1N_sFzKvGsXK;l2i?l"
    ")|9bUzl-WbK#>bZRop2Gl15$5!k9zVe6{;%x$`xY2N7$Jc|*gmtHqUMaJ)U-60m}<7LC|5?{pmtC0-vQr>J5YrjC"
    "+RN+4=OstgE!%yI~C~h$S24-*xenOl7BWM&}aedIGlL~9(N1VIK0*3H-<^huE(T*baYRXT=z4{vu{F1XEyfvx6k^"
    "|aCMZM!BhD6>JO;Rlh%T$y|h#7g*Io@?Kvu6DE7hXF!avtCX^aw*4M^2Vx4N984(QUcQT<9JegSiN?8va%)I_Ets"
    "tlY)h#tC8jzh*ug8lI(!C>6$d~~(s%8Gp)#pZxbM!==1rBn(CF8Wjc94q;3>*@(!24YGwd`~XcQnubT;B3umJ+&&"
    "InYB>vt-s}uF(?G(?^3aJg!Bc8PUQ7-zHQg=vTd%v6QNBYxDkOhgc3d$b1jQUA|?MO<k^{G5r3OxC#U8F9m-=rz!"
    "LQic6qVvhTWVH>pQ_6w=Xt%lMLvohRqP1mBEVOmW1|hHThtp)Mx3LU>{1b@1#1^ym%sDeHtvIXnmZ2)M~$NKDPGn"
    "rFVZi8Fz;zbP~mQm&Js&uY`}5jb1A-Kg&aG~1nyjU=g{$4qVX@kho8Fe|%Q-S)4|WZpN;hSn%m;0PkNbKXUF_Bp&"
    "TUHU#*wy4-UU6!MQ*lnm;)bkq`=BTg6=!_Y&BW8?Tj0w1?ug1_Xb$)IbSncH+q_EdeUjbEW_%?iN^f3)P6uDI^&A"
    "z8D=jz#R&u6z8n}4wCZwLST+5g|(w=lPHBx(MY9{J(~XaGpEEw2X}jF%SS8ScoWmZZkFC+UDD&?I{WqPb{5G*`#}"
    "e);929{m6zSv$KMap4FH1iGuMtFrQ)Up{%aL$eDnb37{w`42yiodWe}j^p6Mu7`<tf=hQ+Q7+XR1>cluX7>=el6C"
    "0UYavPLrXg#^|Cblnw^g~AJmx4ZOA@UQ9<ZR|Os$Uo!izV77R$$;ME;yMee`t~ni?@|$z0m3&->rIV;VldQFPNY{"
    "0l$)Sf%%&%+7lZeS_%-cMqGM-sDDFX{^9Bge%hVI+d1LaXTnek9>Qrk}<hS`zOXez`bvt4mpRA6L2h7flmd#u?fV"
    "w2y_rUxFj{2){Z|t<x%Jj`G;=ur{t;6M~vU&iM#?`KAFH<HJM1%dosZrO(wKn)>I41<Oz$Q@vr&1!*AT(DfsI0l)"
    "{+nekKksT7Z0(oaev7X5*g6$k6wWr{C80vOVnd-#sqW68$mHWVHcq)g$Sf<$ejD<mY-AzmQYz|2x|LPL4KDHUBmI"
    "Ykz;gm`E90hkGr;7PIdYt*TJ)d1qKx?{B&zHd->0fD5r~>Xucr1!lMW=h<ENDCACSsTA*t8bhC@iIfcOfO=I7I!!"
    "0E7(Pi={wmqinC{+7tsGl2?kd;`9n*m+Vwves2o<VXqS+qlDhiGi=gpZKV(YIsr3T+Z7b80qt~b|^Z&l3cx#4Kgi"
    "&u0TQDnBFi)ea$xy$zeC6kGjAObT8%RCxYzwdetm#B&G+jRC|;1&g46izR*Oj`(1_W!>E`iTl?n4I$)Rnlgj_+MB"
    "v-7G4N*<axsV%RCEKL|_EwdsOA%8{0OlfKWA3p&&IiFS>)AJ~8w7#}WP(N}5KduW2T&X==wa+QIz<mHtdziGL-&Q"
    ">3CDOR15u;9~agWzDUHY9T{-Yz@Sc`+*=%b(@rub+JVUH{4V{jdMf$C3O)pI@V&m;Ev$RzkDt;|cxX0ax=Wxa{=A"
    "e?_nHzSEs*_K6TdDG7>nA~s0#*Tj@`0X<kfjkw_LQm&}nTX~~Fa!PMQsyk9!*mJ3AfU9D2ahar~M;EK?Vuc6@KO|"
    "#76Ml2JE|J28#0zA**o$dK4QyIYS<&C$F5Ly(*6td06*{|=!^XvCMVA}9$z=#4lxyClqh(gv;A^PPohfWAUfl`Zm"
    "rc9LyZ``<B+4W=$Qg;Z?BwW|w@cHKd)(7>B}(_(<x|AQ8R<pXe!2iFzwMuM_bMf|n@g<JEL|4M9QlD^6Fj7*<O^x"
    "TK7DaK-a8%dPw}SgGF}lw?cWghDsJe0P_Z9nMo;2bmMkOg0d_|GYgzDM+IN%Zm9XEKCd4oAA3xQ)Oj@w7Imkax=9"
    "?AU2{LsFBHU(c8YW$AxLqm|T;;ILvssRKc`qpzbB-3}s}h5KGf14*n~4B)d%ehUirgu?xy)F4F<pT3V9k)B_$}SN"
    "F0SyBh_Niv{7Q$iSGNaCVFuPg@^fjYdco?70O8{=N&Q0Z#VWs`O{9bO9`tY&Wc&<dFr^Qi_$g9DpAA??*DPRG$v_"
    "w?m@$!flz5eKBC*aXPiL9k;H~&Mb8bJDo@ew87me`Jhp0cx@31e-Gt(sM`=`kgZ<jccepMyw7jz|k9ywE$hCe(yW"
    "o2L(vV#QYeqMm5_S1`H!N;VN8r|l!v#DQf3F%yF|HH2F4qA2+f7wGlwZcLB3G(LUStoyeEkvH2k=A)*Sy#RI;DG{"
    "^<<jT?XeE}Eu4k8|?a^?+X=VTGbd{acd(hFHgt=Pf;}WwVo=bO^WC_T#wLj=Xde5^B>05{u>I2iVe$MGj&;%&}@="
    "|>i&gJK{D*RdnXIz6T5mD1QJ}cR`Edku_XC&A1RkLEDRZS$8&t`V%3wj857HtKXbzk+Q<G5aVz9G?66yDJRT{KS@"
    "Uj(|K;zIFfE%<x_o1&K-7Z5lnOiL}JMcH;bW_XfzYAOE<5&ymtX%u<;#dx_t9w27aG=Tf?krGM=WCU$<#_9XuL#|"
    "o*i*&WhGu7&a`0wKwbi}hckK|dCfh-sYV_I9zLs6hSKbWQv=r4cSJ54&=vfSC1I39Qh`c7;h`-78G%kJ}J+AyzlQ"
    "7qlqYD&@r{z7x<q>khEf+LCg2x8GCiQ1XTgzg|*V_PSk6!4FHUwVl(1%2uZH2MZzsGDn%!Xp^pgt=C~vwo11?EIX"
    "L$^<nr!=TH%D-Obcpoc$W6-Vw2y?GPvnGxl?UPL=O*1MgEj-|>0X{8axLFtfH0y~r?VcxIIh>vO^I$;Ahk5*L1sV"
    "pel#q#E42AUN4zk=R&%OA`4(i0M2(n;n|s+LSt7t_It8ymg4jBGJD(%kVXb|ti4NV*u=<?{0=u@~KKog?=O7pqy~"
    "yW0kr{?44RqxBz?b3PEaBfi=>l>QM$S+-i=djFCxrFU*Nj$ijE@nv<43r_#ynL3mU3vV*ui9F3EoO1TXX6clyiK<"
    "^6Vvxg#Bl6tX2vi!5=x@wQXspADR=q4@oefG|O>dK-_UuN^pH|WVNCWZ9sqzyVYGOl`Q##l;;9tUnSU*z!!sY?<k"
    "rYn>`*brPy;eBfi@g)k<fKT&j1;dkF-V5qE{8~-#I|Yav=W*DuohI~?HA|gT=XPZoHEd#NxvTAM_p>JOIZ`o*(~N"
    "sma{^-LLcB*;WS;_{BP;96uB>{;|o%>@t!L=-Kk$d({*|LB`ZHTlji1U1riXVPz#A}q|ll@OstJF3}nx{f@Yf)Ly"
    ")GDn+8qdgT5K-E6gCWnvMf$<Df2C&OkrJelq<1$@t~?#VI?w^ib2Qv%LU98?+FFm^iRF#J&kc8PSUEn^+HKf26+b"
    "v+$N7Pny$;bCe+@n`>trE-a7Y>^7NBoQ`bgW2!2py%VcGtV?KtnwX1cXn%e<{zZo39kKm~(iO`y5mYzumeA=N%+C"
    "g7U@k>L(~9{l>NF|Km!LYFy>dj&`st_Rqo186RVHDu_U(h0<DX8Ge>yriOq$MAax+hk4(a~`5xx^A4&cKb<nzjCz"
    "x-u<JjUhp%fU%<`1<9`<mh;Re4PCFFPK_!le=(GcW|DOVokEK6T4-Ur>OhP`8e5yMkBm|ZwoI5$1qbm&OP9!X}R7"
    "7oUFD_+xVC;T6wY-O?XxET@!!Xg&JF|Z4;xgMt-xot(3_&_b1ugu(8mTI(aWv(fTH{UfgT(uW;dKNg6Q@F+yP6s<"
    "$lVrA_YVlBO?6LS1!5IQgEl$*Q-U?EO3rmf|_?RbLPf24+ygl`>B_55Q_e9p}_V55)m{YH;ypng81++aetP1CE%U"
    "2l=8$e0U)G41bJt7cx|X`_l44Z>pT2t%voCozq|-@k0>TD=-4hIvQC<kOSQ?gnvWq9NnJ|1Y)4_@{MeQ17Mn%)v?"
    "9tB@h1xD=FE-E)DchPshW`2%pYW{N0t%=Dpk|+G8-CdVJTe<h^gW#Iuqu&+#--86iY9i`kw05Hda8e|9v{T<R>ZS"
    "5fILNj{EN${B%EX9|z?z_FXD;#{o7s)grJ^*cI>S2>r7!NR+M_roc3FN;D&>Y0Gslt>boh7>SG4h6~OWik!zark>"
    "5>U&NDyQ`egQcUEO(q&V}5;mo27f$t5*le|a<xSWZ%x{7MOZbwR6<EZIP6WI+M~CB3&(aXhRCZ~Cm6>*FLAlsISQ"
    "o9VJcHE*A2e4WU1h0inzBbmo(qxxm-#jH1%*@s<IR`Ek4hBH!?7W{X5>dOXP3d<^=Avt97AFwmNe-=<tl}vfq$`b"
    "=59yM+0~|8t2USbcD{*0eky;=RpsCXDHA#Dia_x&rl#t#-aFin*@Elj4z6Hy%bekdD74yfKlbe8C@UbE?$qlB<iy"
    "EY<?KqFDUXmA!n^sS1$jMjPMW5pb-}i$nf`XvhRS33s39@Ee#lmtafB&5tIyKe`$q4H#7qtjPY(9SK1jhv&Nb0(X"
    "cTmQ>c9R&|0z+)dH!n`XM!vab}h0t4pGcXs1vzdFK0>Ka}63v0ys)@dr_o!z1oQXSpZH`RWpK^hN=>D^bH7r)rw$"
    "-Y@;!_R6uaDNthW{*w(NcZcm&x?;m;pmPnRH&6@XqlX|d*GsVh9mH|G1OP&`+;Xc!J5oa$J`Rq1&4|Nc*a_Q`MxC"
    "Y*63Msc^HGNZ+hEPjfwrH?nQUgE4Fq<Z#Y9TgmIU|1k28@DIdrZ%?IK}$xR_Dg^Xz>X|=@qfuLC$r9C<<m1gC|vQ"
    "Zw6(HUbmk2<CeLlaf4rpwmt~zwQ6m1Anv0Pl6IXtGGb^d1%&N8mzz9zmo^C1t_Z}*^W`SM8*+Y&QT>QSE9x%XVJZ"
    "E>1;i4rhJW$EiLIb_uzBjBMD>|}m4y6gsLZI!i;$YqGyYcNf2Ij&Hp|Vj#`Sthesz`2bGF)R03^AS@Ek)92LlJpn"
    "Je*@@oYHxgdGM~1s}@vqDVT->@2<mSR63NZafwoEtlzs%yNEA?*WUgu|fK0!{M=XCf<>7Ebw^GgTcj9%+>i|(C8("
    "||3MLqab@<ugkw3ARo%esePOo*!l_(zA-*Har-v~o8AZ;X)1`-7!wU(X8WtDY&s7S04@q6HE1kT2`+!v-IyYAt??"
    "zO$y;eLL;e8yErU@Z7xs=?eE7GB`MAZwScVb6^{GvEB&A>$$YgJ@wRMo&Ps%F$^8}FzvuTkairaLxVf?}iUpFmD*"
    "xY!3ZMs}zN{=25p5%BQWN@%7bO|n=7SK+UQi+pgzU+TYWX_!*E-hI`Qt67by1e0p`wQ&&Bo<<sF>{PWixH2w88*u"
    "!x9iLJ&4K)Y}2PQ`+KZA#A^dsP*ochSwiTCqN?a8%R|CbktUM{eLv;-!Kc*EH5USWA81DIvt@LnQj{3S#qX*Z3kj"
    "W+9BtbdE%G-%PAy0L8$sFocclqtJmgr)X4)!*;4)O%s9ES$_Rih%3HhHPnQ5qxu;@OZPVL>NN-^IX}mdSIR>1(g3"
    "AWWs6QthcFE7=>>2eAz!=<QJD~b*v-)14(ms3&{f!^%_a0-!oDW{poxK)8p5NhX;p$p5o#1B!tQ}BaGK>E_#9pLp"
    "5HiPELz;FMw|b``nVEbolUHB`|VPxD+yvzY9l&h9eNe>o2mDD`n@2^F8$8x40s9p>Lu|SiD@8e#S{Abe9E}@jP{`"
    "o@FjXiaWCB`qCN{67-S}MLsV{vMx7>C2m$ue6qh`WqfMMn)4NO9xc5U@qXjHH7xd>!ePL|Dm<qzj(&diatv>DFPZ"
    "-M^6151`6I@i{<L@S5^ietml))w<~7OYTx>EVhN!1jKrIE*()Laqg-b+^3WS(uk^L0=E1q>5+!4qV^}aNrtkI~N^"
    ")b*rZYTq3;fUUSP(_`u2Cb`{N^Po2xrCqNw%>UE11U+bJ$LCTEHMg$R-}F|j+r?Nqv;4YVPH3{-|y<{r)U04te@o"
    "s{M{DLF9q}thLKciea?y`*&WJ7nii;1>YpxEX{;pEMe~fy6SgP~wMF#H7OM(%L!IT16h{UML|yh&_NHlHg1|q6Td"
    "S1RB<aTes_hjm%%Ju~eOI<*NW<}Y8<*>8!azEoufRy=$T(l1ha=|>ND3zNU*xYK_ipY=8OXH!w*T}C6!JldWFyUI"
    "w`GDOh5yg9#X4=xU_%Z`SfaPDe}935H}$33Td?9XQS9i(8z3(9>SZRxL?**zS={WDQuniz0QKwxvjv8J9PgcsfpT"
    "K2(V?TYLGi@XXSCZt@BOdI@%Z%kU<?ezZvw3cv4IKi;bcvRZ`qlj4c!V=3I~)PR_TpvLdo~|6a<bRTotsLIO{ODm"
    "vqXLsVNiJw^NP;IITirwwA_=kgdtUUk(mWTmpy-<lA!($G;dLP~tN|)}-xX{ZLTDjQW~YT_(;RY<;)|1Vley&K8@"
    "wndFSni^u=#rd(TFqmm6-dgw*QaWr{XAmMTP#04Kvb-Q9<`CWr8>f*?)&JBNkKz%Fx%K4ncM!{$jSh0R_Lv~w#v$"
    "P4jf;2i`9e#I7M3<qEt;-4&M9fexwl`s)jqVC(o5<P%cG5*>i^beUy93t%F91I?m|y5yM(WCf70O_p0Z^%$^376~"
    "x<NsZCQd|q_lGNJ-^a(N$-&|2kqjq<S$5dUG`=`V*WKiAdoN!TMRy)5M-oDQ*h_wh`&@MNjCHz$yeuS-rqlHy33G"
    "{K)kZqk!6K!t<{+l!vSq8aUKBaKE8sJHMPOKzFlNG2)#I<Sl^P5yvZ}9hwim>j5U+#&1=J)T5Y%I@=g|(p$i5HOk"
    "qmudFu?vPFXG-P^8Atf6G{u4%E)~R?=tU*{2Tm&NsjQpUR<S@jY2*(phFv$-MNh%x$TKJgyjnnOkkmQLgzO9biDy"
    "qgRhKqXk;vy?X$1=>Ts#>+Xq^?6}DLjm^W=#fIc=TMQa0^N<I&u$eb@h*9t$mKki~Jz)-F{S=?mVwGeDsArD%LVI"
    "bjR0%<7ia%Ep}It-Y}typX3G1bO*R~zkdCj|k|)e^vw7N4fES!PU8{KWRexpO;Rs8s$;hkBJ{acn*B+V|wuJ}I^i"
    ";w?EDpQ?R2N*)r~(2*7y#S_B2zkd0$msHzDSqhR?yH3gsMSqq2g`SN_-voow7Z|kLFsOt|-F#lW+&lOgxeo}7$_T"
    "=^OQK}}h5gVl2CnV=5M*EZZAH|yn~->ZeasecURTOHOSn1$*5&UGK1Rt2wTuhl3aI)x&jk^$WE;Ly3%pjc87g@We"
    "hgd?j9Be_(te<1(dYzR$LGoqRyjSvQ~U|am&EcbM~8)bltaOXL)nl6hKtXh)4{N?HbOVbMA|vZ9wzrWaux!LHk^q"
    "^Nb2B_B$$$<(N;x%*`%sb^oE3*pCg|4*=c&bIF-fK_X&JmwbhOVlt$9wgJgA#RIU>Cu_|N?UIXK5kT8%gLQl(izs"
    "%M>H3`#sA0V01XW1!@P@zPv;WSl6z@91-84LzV<-}rfr=s6*W<|<wYcmghi4l^~l0BMfx>|s~t)&}>mY8vx{;j1V"
    "Sh!b=w9pIONUMTttrBDl47DKAXa^|uT$o5BLLSPWe2X}A_;1qraymG3m-ctdtaz@q;i6;7kB=USkp&KkG?T%jN4!"
    "9iKt=|y*Dw=C(eBUk)og?5sZy;@CbBu5z%vI<B)*k4d6w}>R<1k>JaSAGvFzhiN^w4KmM*TRRV6?S=CT{?lG7)NE"
    "tg)eOfJ*8(_&RuwhSD^u-0ZTgc&$`oq7mqzR0QROq=*Nae!%;o!=pto|a?;a~evVElnQHb50{)t{<scAt6SVrk4!"
    "vj!+$roAlR68HPo-b&&)AJyftoy<Q+;^;f&9trqyZ{v5S#t8~Fd!Qb}H#zN_@PtgQXh|AJ+MywN)FGB&a&E;IAqT"
    "TXlkffsR5@+y3cGl1tEVNm!jKx2G`;b#HZiZq2Mij=&#Fd-2w@SS@xQ{^TkCY*M8hu3M^(gVSP)FjGfl0z<ARLsr"
    "7GAR?LfF?*JVKh$j9s?joPiX-FV3m;07j}k^eVMsPP}<`wpsUWQs<oRV{U2E`U_{O8b9H_Flv`NG7&1la+(EYE=2"
    "Y{E4Cx@KJ&FVsBcnJtYKVY-YE%~@yTB*??DTLoHy;+=+=h$-Xi0`fGmpAUwSRM(5n7j(|ws9B6Ro5bXa=1sX=XYy"
    "3@zgIl4R3Uuytss7GIz38v5S_1qd5I45?LOqAY;OckiLP<<CwAe1!$W^H=Y5OCYp67cN<<zSY;S8teyMt|biD%po"
    "F@db4f%*&=5oR3EP{jeg^aNTQepF^Bv;l^w1fLOERD#9C>gMJl^^?G&UcO%bpcUzZBR?f0HgPGgCca|V2vNd({@}"
    "55;g^#u8-__UX<`T^Z_q3i_A`B>b-<;`+l^!@{o<UC(zUS~1q<_YiW|h@FkOhXacVFwu7yNe2n%J1(#)|F@w{Fyu"
    "vo4*o=(Z$S-JL{eV0E_2Qn#hsE)L{Z%_VW~9e+yL?a1#}_l5@ss~4ku9}CLl_X+zPKiw)cH%pW2F-q6rdPzedimG"
    "0TLo!y}I9J&TBbVj`(GAaFhYKkpW+y{Jflwaat>ml}=lqu_k*u3)77MMac<uDYaJ;isx+LX;*ZwB)I)kPav8<5|r"
    "PG2pRX1HOJzbasM+2&6jGbf(h0n4oKEUTi=aZbRAjQVH*?z0dZFWf2?*5@yw|M#6y2Y!qX=3~R!*2HamJdy)yfc`"
    "ZMz2};KXe1L-@k(YC7LvU-RckEY)Y}?I+3LT<G%9=-hytuDQ{C(ax(!N;8Wdrk&mE$A-`4c?>n{^<PASo-5TvEu9"
    "eQO;-aN9&mjg#z^9+wDcDp4<(#}XIK6HCds%RplAxySkXWo_6v)wpZ@rYRCQ<ZZa3A2_R#igDF3s1{NRAa-9{+Z*"
    "wV!Y3f{CwcaL7oEv+Cs3D5#T0^ot{x>M6&M{Nb(vs865KuI22i55^7;o4WU0n5z0I&I`tGkKSb%AlkROHhxZ5?=8"
    "lXIZ>PJA03hip`FdoZ!It*87JV_k<RX+6?~>miy~kc4N9*@gZcV)s5wDS=CHpv$V9nH=b6IAWqp`!{qJ2AR}yHNL"
    "q4t&895_;@4#s{N@;?9yZ)N2CQ;;IlR8fW93pxNi5)a^<I0+4=9DjSf=DVX3Eye7F;f@2Iv)S?>x1Jl@!$8^Eg3u"
    "WK4d26|67wzyzq<|0f|yJjWq8^6<xEp)d+o`Uz-smCNr-qdyLLBS56EfN$t@6gdo2vxL#-Gng(l{&G}}b+X<W>q1"
    "bHh!Er<eKQs@adM6Ys&`kCa7tpHr)oJH8-0Mja#miRUsbx?qVyo{e;O9i1XkPAuw>;)r@H4f9p1m1}4vImzL_1tp"
    "h_WUH!?YcgL>T~L($Ud$aa<aj5d4D7+0qUXgZOa&G&~nLIVdP+<I`$pgB|f(Ab^H)@B%tV;VGGUGn!L|SS|3$N^b"
    "VciWCPm5a?Jk3XwSq%w87d%hLWL#Y;fx=e*&9Bw)#5oCp?0Nu}ctO;oKr@CeR%ne*wzX}k^6F_pBG{w4T5FC_J@Y"
    "B=9(DelTc@qQog>PBVAdOqE(M6HfAepP9@<f1#rlD$pYWLE#I3~AONXPd5XGrPrnW!Q=)Bkogdl`p1GLn1u<{D2k"
    "TzLP3iQP=sqSQ9@usTAq4!Wl|?FW;j(|3lTW*b(7RhbUB_s90`75BlgQ{kzp&n~KF=2=II+3p%`PoJk==VGLZ&vr"
    "6Jfb-iUkAHAqpXO2nWDV`O<*SF;0>Y!!B7uxHI-cE`)(#QcPY#1KA)Nw^|>Ot%@59!Qb#WRSx(3en0QG(*&_lz-V"
    "+RMzp5O>CG7+^-EeF5~HiViv9H{V&SjrCZ(TZ<A~i75Vd9n|#A&>PyQat`fbt!m^kXWP1Fhcu%cc~MMb*Vwq6`y2"
    "0%_x6+Y97#t(LYLDU{|0?CR~Ly&O~6dp;#9OKuX%<VhB~YRHAA-)S_D^DI=A#ZFK78RP_nsoc;F%)8UY*DME@$gq"
    "P=!=nQFO~6@od*tQ3XfRCbT6CLtBk9yW$#CeLq8njW+mInbOZBE@2Y)>Bm-nfIx~x^wc+FLN%|Mr+zWfEJUC>r&R"
    "Y^f=W^h!qoSSPNLp(nm2Y4M;V1#Pp{Um|*>?U$F?3%Wz{a2Wlf;CGF%?+EPjRT3m<*EI20m(p9wgB)|~nw3m_$=p"
    "n5c$AbvrLtbnEK_r1mE0L3=RaS}tZIWE&^FF7Q&6M4wh92ZS!G;#4Qj56d&E+ktG{uKTProBW=LTw|#s=p$orsA@"
    "lRt*kKCHW1!)t#}lBd-fn^d!r>Q`2>Od@A$t0T4T!m0->zDi5)J@e9#mg~y^VB#I$1)O2a$N`J;<7*ASA;U{s!Fw"
    "~NdS+UoVCp|nqx#{?dM2G3_QNhp)-DQFt0!zrmV65(-g{NEldi7U2TS9S6t)Z=y=GGpqM|^wkI?A!tMG)sr_=A;d"
    ";LE8Ig;`yI4Q*(0#uAeb?b>hQaRPEYO(CW5$nql3+0gTQmI34Q@S`KxIsiZH-lhY!&YZRXefq)Px7I4N=40EAUG2"
    "&bvgHgUx-;}V_5XF^g+%^iu6J0U$AcSQ+{D3P_lztQ#7532!9N|ZcEo}tCJ|{&5&^nEZwMFg3&5+Vpr?_HNsR}Bg"
    "g%W00gMnLasUJD&YZuWpT-U9Ta5bx0OujA4Tatt}^$r%m64{to)CPgW&$$oT-)JzCw<|dA{(2AT!ndvDxJFZ4H;i"
    "!*qMi=73@YFK;pHuaZ;Xl@MjWI@nL1YO4!YFysxSTS~GQSXr;>N+>m4c_An#(h%V*@d}YzN<=TFhn!2OsLvS)4d2"
    "R>wD@SP>ayDp&dn&_qe5Zw;^^>n@8EEJJUKW#I5l9>2X1wH=%LWlwa_lJ^m*V4AczP5UYdahZ57ZqWp<e_aCuP<&"
    "Qa;!<#q@9?I^K6y!3OKt$~<NqWO*WThVXxdFQ)l&%XIK`gT+Q7Si<tKi_wH>LqWgU%Y+LKM-T5|D*i-IA7A@qnp>"
    "oD!n2imzFO#G|R01qJKo2I-U19fLbm=`mSvwP2?uc*Vi;Ze$5`f`Q`BFFMEf7_HHP<F<|R-*#ukHd4dac7#WrhAO"
    "FNXkgX>pmQSSHQ_JheR2eCz^JMS@-?}lMevO6lXDvXl;d9zCFkB!9NT5IsBr@`bpkn>|QO|m7u)*gqEJ?X0rl<{q"
    "^yXrQ!h0O}hLmo*k?Utm-%R$I<p8C>=2sh14Yc!6&IzSYzngsX{kJ_WEN*OvtRV}QotnU=c=P7G<%CAGIhp4x<`K"
    "8gk*3edw*bC_OO8Wj#dXf=zR$<p=XauYAt@#n3ok{&*#6=YJUWr?*C|N@x+g^B<T_lJSB9=rHX@zJ_ecp@knAf2l"
    "S|s$BD-pJmXoYq-3ssY)Lb%dzM3OP(zzu^R^M8=4Yn_^==AhU3siXSvw7KE<w}&pjnsa}t<s7zCuwNyj8~*FktxZ"
    "hW1xGi-adGf_Wyma|G%H~|M1R#96TOQ`tKh7V|kf={p`CT{cw&8K7RM@9nK#wUqg0Ay|weJqmzUGB}O8<t`_+$U&"
    "k^?HzQ?{FW3!Xzw1uaafi;&AC3GFp#J7ba2n-RpML#4eu+sD-+cFM^6Z=MqU+J~MGlZ_SI+HUm|%B$!F<X7nM7r-"
    "Bu@Gst}<%Hkiic3#1}tVrc1?9ax-wRj@jt|n3c?b`*ds?a#T=W3Pks_TVTOpX2HZh<f}r+iu=#M+B^LV^bc@l`Ax"
    "k|@&ofkVn7h0UEha3WEYV_jGYL69I$(#gf&J(ZkGA4!^e*w(`*`*<mi>w$XsE^gua^t1WthnkuL0fm-uHLwa*RS^"
    "3B@^`zTI7p8VzL<dnn(vi$r6-RVB#USm$pKoxI5f;5WUq`o&k2=Y<VzufU)Y1J2dN3Qtzad0rdyNjDk&C+YuorFx"
    "QJ^awNsrH?;FCIPXMejKZ-Zd^&%C-ODK=en@Q;mqU7c9E?hKG`lh%Ronynr)pvve&Fp9jU}t`4~yNtXLt$w^o4(U"
    "amIo;>MRn?X7S-$<ZO4DI)<(hcyxZ#&(=W%g@e=$kG$I7P%5?04U!MThjV^ZeHl43J{cXLOZ(HPV@~Q@}}<kd$$d"
    "pd@hPD0fAdyKV80p_Rj(-g+pK7R*4odyt-ye1I3By92!&nd{7?>d~?vMHtYck-X>^*U~viAg7@<hqSNHmMySVe)g"
    "<VF@x2@iuYU(aT>l;^%pz{6|G)UWtlbq!UM24Z9&#ECfIP9Hdd8UD>`lC@YVI>#TnTyJ$A2Cze*dSffbeweZ1Xev"
    "rAg5&XeNXZ@&#YcT0*Uu=uJT7{?E4;j_)M;oE+Hb=CMaPrH^MnqFm1*NW9PT1rfze!-%+=(G2E)qV|^ut3>r{FN9"
    "JjZj>V_Flehy&#>>M<?S`GJEd3<j*aakSyQO#@vFKX{z*QH~njxIPIfEIO?~Mo?iA@nvK5sy73BeSB$><wt1yz*P"
    "C+mwDG5nO3B(!%L1fDLk_?Dw)xJI*80itN#l=eVoOag^O$}Zu5NnE0=$&|DT%H1%KYE6(f7@BzY;$|<(G5fYPZ+f"
    "=nRgAay1)$tZ|;Z-n?9o#BS<g>sxo84#w)1+XIYRI<<;`tKE6fG~AC(uPxSFc>3%3$g1Uqr~h5l?U7@Rk*t0NXun"
    "Ps^odVy?E!Ph(D2@aSL6Cc*=iMDbaJ|X^!l`ZS-uRf+8_UoYe3`6nq_oQlDt|^P!?U%5X9CS+W7{kCMfr|$H}_{d"
    "aY=@BUby;)hfLW%Pg(A3nZ+=?g?d>c_o@X2D&TTkn>m)J5SDFUwrZ>`i1!4?dM?w6rKJ=>dFPMURRy?MSH>6<G+m"
    "$PbbIYz5Q+jtQ<Q7u#CfIBr;V~-2>%Ahb)KAlb&CPer+9UV!Q!+j~Dp#;OFt=<-yMfr%k?4SE5eG@qP2pv&+r$y|"
    "^fFW-CiEU~yNVH1yjifB3Gu^)-2@;b+Z4U0tM%0xy6EYJV227HzalMoYybu-mfH8GH5m^s^QYcCd|9A@PQX*NNA&"
    "jk&h|<@JVRr(>Eo6UgAn(|c&7b%iP#_^t$Gx8lW~e*LYX@0=bTy_^WrR?}K3#8AMVPUSVml1MUa-ST^=_&n$O$YE"
    "{$?K#&4Du7#H2)D03kvlp}TwgeXzh+Q9!Ph%E`14;6UcT(MzU(Wx2@vv|>v01Nqu2P#vf8x0VZ)zwn=jH+$i=Ol$"
    "~CPfWQ!@uTA|sDGd3!r{Jm>zX<ijx%@U_shP7YYWLfSey(;hiRWgN|JLPOb-+1E#JUkqY=hWE)v6#_~5XekgSAF%"
    "cWOw+W3df3Ok8lHwK6z=cOIunZShvdgVl5Yt@`RNh{hyEc=k9+5`w-ghhxB7vHQ#qL<F}dfUwrWy08|$%F!`mT-M"
    "&}K1z^y1r%9Ss-2!Hn&K6m^++1t$Q1e|#B{<JlSAhdSLscI`6aw*rvyVv|0fxWI%HdZr(d6$p!&rd4>kj7J!Cm0Y"
    "(0`lJ$8cb}(Rk{b8P=3l+HJ9(r0I3dJW{iMa%B-YJfg``LN+HahFlaZf?jmDB}5l?C-wolQw|wLeSv`-KXe#omi;"
    "Grs68!eUCsO4kO#LS>BhBJ^^dU>e6*)9-PvaYYXzIaTxodOF5_OSfJ;s!vz}Y8_n-8?>s!|d<k0t|<oel=(;9t~A"
    "m7+xmTrLU$yfv^$z5J>uSv!9w7Cz1L_)n+6Cf-ln&v`wI?2P+u>Esh8nC5|BWq(F)>u}e206?0Ej~Qu+Vt;(&eZ+"
    "4OO5pQ-AdA%xyFa^p!-f4(u)jvW!%h0J8YwqwS)}N<~iY~W1l#)T+-sv;!FC->bD+CLbl=UvMH^8k<Bl-$y<=ly}"
    "S*g^U}u9HFuUstdyQI^+4LKwKPX^+?b}H+gDKq2NM1a|5jV0Xv(HRkm3ZFia#zOd;-M2NdG-Yr2}q3d8@`CIaH-E"
    "-rADFL9Z!@`9zXz`8nLa`0GJ(0yq>$_E&KlHn+S$3HagomnltURcIfp+W^p{W0`}#H99!EB#05gOa)d@5L>#wD-3"
    "U<z09>$QOVI(+>NfZj6N1(iCP;;Gp{-vCsJ?qZ9wU|xjd-oaIR@M2_uinF0XHcScwL5GB-$R)l>y(#;w@dNWh)SH"
    "Uzk}+SrCW>xn1^*ek7t;-B_hq9wy6BAEl*p>-id2@;*-L{A3FJ(pvLG!rFM^i!lMl-H?ttWl`eR61!(qwK@rU`n!"
    "Kz^mf^UKp(BYC{l&PX)MAh)VlmXzN7{3^;6Qj{=OejfGWnFyO@!VLzbR<}(e*on+9c#}=nT_eO?77mse-b(y#bpL"
    "uQVw$8X259eyG3(jZREV0FMY{IigGr2XKVqP&4H2LD~(w`5Y%_y)xP53!dRsl%lk!AE0D&fn)6Cff4L{Q$L=ow2W"
    "F=3(4jc+udT^#4n83}-CI14-bYC#y1DM}Xn@-w$(wwh$Y^a~O~nHsdeB?!#{JWGd1yk*!vh7K_C<T7lq7@{m|PN!"
    ">K5F7yR)oA>Ek)5w)+4(g-qoZ|Gl1e4{L>SrbO|6?@Gwph1e*X=CK|L4KdmLWwM41&sIQ3-P?YsXNl+o>tyXDEf<"
    "fOP!_|ebo-rabc@-bVu`3Lm7n3SzEXTf5ZhqzuX*E_D6xXdWYjSSc+=Ot-LR+asWZlU@Rb3HkS#BG7>!?60jgadU"
    "n3d_kGl!$SvwVk9nsaRwdWa$-}J(@5A-(`)3j%m5ZzjB-~5Y(tH3pPD~&|alM8X0&CF2e-7KsI7#z%R<;5$m&@vg"
    "I#F$B56qJUWqtra+L%Nj^Pz@z=@0;pzDJZ+kB%C*v1Khx-7H{d(|Zr=HBm#^gNZ4BL7}>-WNNs!hFx=-rn)Jo>~*"
    "w}viK-0z)nUcnCyVV$|$JSV;T)k=X|C0XUg%Y*0Y1lBKUPs&OcZq*q=oys+z=IooD+D<DX9ldM>WBQpRIUy6^V!N"
    "RlHfQJF*dc7Cy?8v~O8LtSy(EUNk-!UXE#cr(wjfs?XJxil9n;h@10S=*QaT0<pVq99`daF3iYFgs(>@vh%_+1j*"
    "9Csl`U`S58_8QzJCCbiRy<kNyS)C(ZG(7fd>}7fTYFtHE3u8c^PtWrAwIQ%zw_kvD>{S+Cr8KJ1gKV)?Nynz(Dve"
    "1fqjHaY?cB!#?>CusYUDCcyFyzM7jt$%a50;3A0JN^i`n~d6zp;Ck?Drh{|4pXsodTCWRWisDMNT)Ew4iMWg)|sH"
    "k%?sl8J4F&Y;M;v|STHIeINyc3`vcoV1?mF5#=Zh}w4;BUZ$=DxtO)quQH=&AMcgP<6a`|5I?(NdKPHZRR?Eic7m"
    "#C(5I2>cWp?B0)IWsalTg$K(I#QAdWAtM$lKT5JRVA)D5wM*x#5)!OGGsyJ@r(FR6pH-@+B3-4n)&{K#i4~I^X$e"
    ")JW#5^lk{4MphVi>*S}W1RH6St><~LFotig{m(kIc=-ZIqIturWcp=S<WjK==&yUDbgLGG=r#Dq3*iE7SBjJ3Dq*"
    ")D6|1|7v4L||3=h^IkBN>f{!``r#s{v3uKSPT_HY;kW5ngYmeMA%!ERvZ;U`qfl5(n+w?krFrE=GAZ*91L5)ekjT"
    "B;lIVpusjDmuoRINAM!by{FcytS=@*dAYJ)JLq1p_(FlVvU<>%7Kx03TNXg@`IN4Bp(LhnRKH>`|>%4S0itG@;`l"
    ";_zODVw?UGqSmQL4*4j}SQCJ|ICTD4u5w=cgNU;PFl>@D)Sb83tO64xc(|#OPMDT`)S;c%IZ4|I|6q1YJ4=?TBhT"
    "%b>-(S?O$Au;t*~c&2&PCCrqLcX3^YM@xGZ70b|3DBTJJ0%)`DG0rc}Tr$I~bh-{pp1q&QQqZ>3!RtuHQ>mUIgNQ"
    "`U(a;r~YHNGzYA+S1p_ig(<+sL<ILFy~HQB_>Op;dv+=NuTTS@<!^)WIxRa$YK*_G<2W3$o9@b$ssa1k)L<d*b3^"
    "}{vlNqVe@?fj<FZq~ICS|;~zb4Qv!E6W@4|HI%?K(3>@DrPt9XoDv8=@S|f)f+lVXmU^0Z1sLF&8mw0UO2{TsRpD"
    "_9ZLOqtf!)F)`v`8v$;6+4Gxx$%PO5|CAbw9R0m_}$%@ehE=I6H0By-2*wB9VW9r}9)NUe5gI7J=+6D_3Dh?h&Qg"
    "!C2@d8VLk-1kY>O<JgVTA<fZfg@Jw0PXwu1P^QMverU!QYJckMLT2O{aQCci;pB=%w;2$l2XnS|&wJW3VACCkx#+"
    "M-7Fk?z#=^ztP9LrsOVZC*fzJZ7S1sEl+GNm(qUJ#~~dF1&IvCP)`G_ir>Ja(sHTVtfS_F)NxIb_-HQxD3nf&d*X"
    "hJ>Lu^GjfJ2zx>o@Ft<B}acg_<m)fVOtmLu8*UE<iA9dRFGkb|Xqga<7_V@b1O+%L_8Z;ws3*A4R)gIeG_Bzh`GZ"
    "{9Vh`Gvk!9Lz?iYe)YG?(^bD`;ZkhPo%34oX$;}$79J*F8O0{DBax=yz5uVFVX~=gT*<TFc(EnpeU;S3w1^hH6oM"
    ")wZbWPnjSLIB94jTiEw4q^zl@HnWv9mkP?p&(>KbCN!F}@m6k}!aT-l+s!!yEbEq0*?I6<Z(8K(SU@at+<w72};Z"
    "T9PD>!!2rBMb-*FO6DuY$ZLYNMl-a3~YWqRr5<DVoOG^emzq(j?HzkZC5AZ*IZ^u9hf~G%3;S;HSKtl($!leEGhX"
    "!4Wy)JMNZVQm2-BZ^W7;)#S1eCxI18ND#Y6h0YsE^T^&lcvs6;%}eVM-KmYhE$X_l46~sFM|;N{`}GmJ-s`Uu4vz"
    "%5hseOVV^1p<gxYcg>ElBJV3iZ+`S*;aoGc=n;YNChV}$3j+In_pXo(13B6Pt3VZuW}^paM!UR%(#@U1#3*Oqa9X"
    "snEHX$>4yxTRI!$h~MCEzN?rX$$TeCy|;u0^ge~wF7j69O##YW@LyiSFn>4u34xL4@<{S7~<K7Iv$oyg9*g)I_sw"
    "^R69V1MwV4KGC^3GWCgQnET?lyD-y)kx!jTyABEL0W9FYxwW_^C8s~MMSbR``qn+64`R7R3RzlDc#%_E^GvB;7!8"
    "IQZ_O&6IuBOr^nvWnUZPIzIMz0-zwrXuK0~&#1Fn)3LH#!FUQNdK8I|pn`d0POCQq#Xb;XuQCS2@W^cp{t6TX3>;"
    "f|bM5px1Aw`z`3Zp7S+AX#`I)&r9Q^9oj`@C&E0ys_eP@J51UUW6P{tx|&BuO#QW5Z*%cOzGoY!YQX;q@3{}~MsK"
    "fJ02ra&2;d~e_BGcu%?XpHKN<e(d!)R-uqxhJEzL-2f}?w)*9F%{So?dSPiM&;+t1gAzh*o)@>j7X?lY1GRb?>_s"
    "!uH^NPIKdk`u6lFq&#vkHu9JtBdSVSO4EXBw2|-2_K5*mO>})%en(89H+^b6uFTW($2Hdixj+`r2CBm+m@pSHRCv"
    "_qY~Gd!l?$@zxmY84f)vja4>s$ZAG>dR~H-V9JPfG6;T;Jwsz!P4&<0u4tRsBstJgGi>o1s<&Q#f;G_8?ugtZciA"
    "s3DF%uUgz#erzISRlrfUP+K$D1X`fq`ud3L>+Bd!a|k!l-9pz#fJaVMs)d&=uDLq~u+J=EPH{@koO3!IBCzymOd%"
    "Z1)CFV3=dj=mU)E(Iu75p13t=-!xV=m%xp*Jv>80wT#0%SzY^JC7RxH6t7>{TeKltV#Hte8i+ld;>dmL>-PiLmnN"
    "cm)Z?U{VRBX!q@ZzFi*ytZ%+i=K)7Uy0VITOwf#|cGhuN4fULGV|6Pj>QsC7LnF7jCqU7t1pU%9wWS3&2uDW=64F"
    "jLGuXoVNkFLN{n;-YORE!Vgt`(G6;aV;Rl#SCYX8>FUQrR!DxE4OU!DVi-(HW~1OQJRo*sK>xJz@uLzt1r2v?-t^"
    "`^6rIoQvyD{sEUX|_;w82G3C>R8Q7zywhL1SRN_>5dRw}b(>)VQm2hqVzHhaWqW;dw!Jld0lE=x5^=i?7!Fa3Fzh"
    "<{*MY@_F*rij6?9Q#1m&8P2*1nfMT?I#8u&kPXF9}~@<rY<uhzFa<)~gy8j&vS#E)L>8L=k`);1RDaiWip{(6PvX"
    ")nieW%k)ET-nJAvEBz{nV)=YdD<YUYO3%aCK_13ufJ9{x8<0@S2&n9rf$NRkGR0yM+EH2n5M}?mCTvY9z(RXmLVz"
    "-v(&5#h1EVBKb24z!K^1`u2SgdcfNU+6{fmNVquUUH;msH&OgeT}I7xu1F`JZVjJWQAL^oHApVXtbBqe01Spj@@E"
    "5Utwq5z>_^svh@KMRNOt?QN`fUEjAs0vzBC;xPOg&h%JuQDyetcuF^6b)_U1YaO5C)Y?^o5&>{`6mwKF!!ofdND%"
    "|fPJKpmrHf&l`5A92wHaV>NbAEeJ%B)+g@jfSBfXE<%qRYJ8Zk5UQ@Ysd#c+RW}P(5b6AsdRchj!0?~I))|x-xSd"
    "wA#5e2?7V50)iy^EXMcgjltBfzN#V>Ag&8Y4(}zi)&_X-Y#h<+RgSHd5C|Ih`4SX0uxc9fkk|SSp%HsET}a$uf~9"
    "dY5!u{KQ}3)X}?M5@bnq*(uRhIJV9f8IV{efKgs%b$rKDy}+|;y>jRZG-%@Kdq(2XI*0V?EWg+gAvt*OFM{#7x*w"
    "CVhP>EA@$R~q6^pj~d0tvrm}|By?A}SX{I^ZE$-YoN{io*0U#{2J6E;Hm4z~g{CxA=gKS>1su~>KP70qp*&e-+nv"
    "WZP9piHVGO;3<cSy(?HLHLV-^dwPnc{@bTZ1_MUh+!aYCZvC@Clei8dkR@1T1C1jd_aUC2i!OS!u@{eG2<rvcfW^"
    "6T>3HGk8@<mX^vn$nqOk2w_!v8>X(B>4v@LskGhKX>!2j+M#kI_vwGTn^W@!cUfXC@<ThTM9Hp)g$kcv)jSN6d&?"
    "|{(6w>$YgS-1zg!JUi^))v>uO8!^UFO?RH&z)@-m*l%M5(UP4+%OghmRkp*ZIJB3F;vppA~CH*9zD9_rPl5Z{=MZ"
    "+(%fhQ3c!1L)kUlaLJVf<>(_?OE3yk|Md1clNwr1-<k32K9(@S-Ih}6Z=UT?2`#HKP_WP6jgqgQJlUb%*{%OPn*r"
    "fr-m($8^zid2#vfp(%Z_{SSuww@&x?u1d&*>l9+O>HDz)*2rhFFf>5=AuX~8pTAg51z1@&j(vD}9pA0q#rDl;8jq"
    "h9c^9#kCtgw5oS-FoKDtAphA@ypV|n7M8R15HLGi6r@pcoa+kz8u|5ig})ugQg?YuxEMzv}eV0Yt8C>_2^5+)<FO"
    "uiX~>wE=c%JkK*K>i3!uP<30@&sq-ka^&66?@2b30ciCOfZJU<29RM|TSYdK|3YgTw+VuSqAhGA}&)gec<vm!GPM"
    "(wPkgdpQbt(W?dL!j4hS;>1WTcKbJDJ$Q5VES5Y=7Zul|=h`b$$B>K&Fn^foP%$Jcb@=JUnP<4j)-N;NOnO{^GgX"
    "3E2N+{Br!_G<lT#bbR!4;&lz3w>iwTDVlsaLfj_l=wH3iT{vLeaiWS&Z1~8GK!g10jb+1>2s!;ptQ!2U(=16}!N}"
    "#DB-?yfwO?=-IaG0pIek{FO~Htc{SIq!aCkC4K26BhIBH!9_tw%5K;NR9{B7^$>+wm_`JqSuHMNI2I!s<19scz4;"
    "Kiwp(M|S`wC@}T$#}>SH`<zK^Fj0k|Fv7VD!!o2OvdSji%R77?UM#L|Eg`vToJzT1-Cnxb6Lq*bS!#F{G4u^DfcM"
    "^`w5Z7{W0*3K8;*C@Gq+ylWz11QJYLNEB#WaF7>Hwqvs70sdm5<RrPITDK2+{)^6*XxWikVpQG@pWl40r9Zqol^y"
    "<hXofPSmK7~NSB5KKRL=glE8?iN3Hp7WVs-pjalp=WoqonXBD3S_FI82^Cd4j)H0m3(5^B0QbG1=IdLtx-oqksqR"
    "?rMmz6$M0Z?D67v4H{X$Wk}>mYuZJfmz$F_7z`fJnZ@mSjx2tkX#9yyT2_)kygM_0`uV4WKP!j%(+{7-V<Ps_CI="
    "XqO<rk7Mz0KB63DIZcgWZ;^NUMpKO>{oe%N;inuTr+sTR7!!}}CexlR?--PF%Ef)GDuO#_u*CDtsTRr_^6)NY|^v"
    "NGkas47%`%s(biK5f>vL`<*i+uF0gO7;s$&d$pjz;2Lmldcv-*<>tTok0YjOS5GLdqEN^Ln3p1jWCSrh&1`@jfRg"
    "yoDGS9NNObNIJG%aV}Ls*03g-rUp>DXl~?hNJEL`X+@t5aakdkPUj5rB#Aeb$BBeAi^nJQyqFkcWG|Sl~$H3yN@#"
    "T*1B+m=1vdZrm>bJeHzL7ZT)@|=?QGK~u-=pC?0A8&2zWB1~<TU6K70V=Ft{WokNKL32Ce7F3oop6t;&%m;5%|8G"
    "T-AIVPb0XO-*o$os#m+#)XkR*>Swr^<%Ino-RA3qJ;!oZvst3a)9(hW)_es7D_`Y14*YQxwH#;zyOwAnLNO?bfBW"
    "F03ZJ{-M|ZaGnlT`AZY{B6`e`IPiCinflfAAYGG#WZJjoxuhSzSEe!hUjbOMyDs2jJ_2FvMF{PcO1mEdjXE)}v>f"
    "j|y4bpQ+tr8msBVT$LP4$kY?1}E!v8_QwwUwui#OQeT4yjaRd7T4$6TRc)=aH%fZs`Nm<n3`%*=l99eZnw3dHdv&"
    "vO({nmCLoZ{b3^z}HM{yDK1JtTNoCaMI}bETwo%cvkjv=dtMTFf!Qr1DHf`SV{`ffg@n3Kp8HqJ{+R)ao-J#OkNg"
    "3rX>y2=&x_fb#NQ(><H|#M~d<rr*26;KBvxz=`EGX8U`ZZm1ocoRaEs3@DwFW`^wcQ^d9*p-Nx@24BSu!uqWbAdf"
    "I+Jw;U~gljaErc5_B4sY5)*-!#Z{(UlWNhmp0xGhWlR2YdiqK_=t;f0Yf-u*i`enKPmHE^d+|m$i0Tz`3;fxUUsx"
    "fZaS;r~Z~jp8uj~Ez=gsh&@1Ky-jL5><x63yQQ@CDjmPlEhKX<;{6eazuHP;hyK=xgnTc|E~Z(YaX7H+o(wLnvET"
    "ZoXYY1WX2Jioj6KvY(Jo7cWtIwERJ<j40tnoXfmTcvid^TUU?ykpmJdoPRzg_BK3WTq%RxSIVavSxkIz`qVpeTHD"
    "Gzdw9(aQExOzaAd_a%cm53WpW_W&TOMSMMSHAA0(-qaOm|udrM@9=r5Nl{amOM+M=pkMWibTXyoUD_JSBbbjTxwm"
    "uDy?5=%DL14PJuEJ&5!q_U?=Tc{?lN^3hR{oZZeBQi)B{Gy*Lt~4rIr#?SD+`0aCQYjobYzikjP920SL?+5<?f4Z"
    "PjJj-*dQ2N@7slFc2C|nJR~W!XwM}nip6A}m)Go=h;WFBcg?x|r^gZ*va3VWWXeRFm~Ga?r435&8YgZJ42tE4Lc+"
    "MeEs=z8nZe=390C1IW_I5T;`)M}dM_fQPd4#C{+x0S<EvHi>n#VMx3mJ4_Mx})6!@C<+mEE6{*2-_=8Qo8F(+MX="
    "8Dw9i5@J2oYE5GMRvlF8@ncgxNYd$Wd+!DwE8nLK4rr^jNR&DV_<9au5aAjRgP=^*w8KNn>WaNkn9Kb!XuhZqM4("
    "ml5pIV$XJrzeU)-zMSHi$W`uA#32T=O;D8e9m_YugVH0~0KzIDe*$fR$l(cn|Uo3ZV@Ll6Q=(Tl)9Oly9;#OBT7_"
    ">Xlg{Y=LgeUecOw-xdbC|7~5_RHKm#`Zg?L(<>9x;7{{NhpYSz`sE8HHd=aD{-OOt@SyBncx{q6>(qca6P41xN1J"
    "iSRJ#w^eHd%Dk!}*NB&sUkP30D<`z`k^2z~!832-azcDSE&=Yk>(=yAKV%o#AFQhKUpsUj#L#$LDc~GuK<dru48("
    "ob&MR#vqgQ9&&g99r-%p<X!*{zUMe(Cm$!+M~=yRTAGkfw^xN#`yu^+?lD+AQ#TYrW6@h<)OX2OdPdBZ7x!#ih3g"
    "7;0D&e`sjob?oJ)_|sZRl+%j^+gpHt_of`O6G#Rd7o)I7tDd7<E-1c&|277@LZ_s7=h_5-e#Gs*vIU%wad(u4d>U"
    "aWqp)vo}n;KSRaZ&HcW)xCN$JUhj{zoZd=BeV>_JjM(bPULk^IRC+dD>?-wnI371NOPeqv3vUn=L^I$-DMO~UD_5"
    "gmyPY+(tGMmv7)G~N>SQR}I6E|M8EV?a&NIdBit0!WsYh&vi1W!Sgo%QX+XVGlkp~lG#8_U)*>3&|Hu@&7lHp+@G"
    "=Y6giqFk|T1fpWT<Cd~pg`R2XR?8#Q+tt?IH0V|vHPdZmGfnZ59ri(opqH5}=q0jf{hJ1n9;0s`NZ~ep!5{AGS#4"
    "o5n@eE}^V%wbSh`BvD9K-HC3ipf*c+nH-F9`ojMVfWQL1H%y3@`F$xr!m&Q(wHi`2ketWq4tYxf?g{bA6%_2(+-t"
    "KF3EHY9M@G+S>uurFR|p{>h0A=_?VvWv;5DVyRljBTC_)eb04pTjGp4X!y?*<u0%FxQoI=-NT+{#0H2eRj*!ZGuS"
    "d?Doig+e&?|DtR*ADVO?TK>Kl>E+(9pt(unk@YJU!%6gO%&a#niD=xNWg?r7C^~uK4Bi4>aD&Scb)|9fkuaNI@>K"
    "L|6zWHK0nI$ocBB_O@qGIruJ?zqGkzSq6(*&BvkpC|-zZ+^6cB*ty=s{>v!+XjqnW?tVcy+297wU)51o;+L37_2m"
    "s@~j|+w6U<n(!%$xu;K}H@``j;z!dn!xIh*l+xvUhyN!8#YJYk!y)*e<%&2B%`a(X>NLw0M9eqIBi>J)!vA!~)<~"
    "n;5>IaY{iyw};Doi_{B_G?-#!53)xQ?GDEtFEm$lA(`MC_%7{kYESv0T1m&wWK*4A_Y0_)W1s?*26Z=R6R#2=o%t"
    "F6U3SKJz%I?HC_)nj?Wn;{dzyL!Euqq`1|)#C+`o4U~-$)ALn9F6}YoJ9Fd^7}p6n_ow!BighT?GLMrnn^!klO9)"
    "K;KpIf2}q&#3Tx(3ZL-g!UWM|{BY-aQ^K5oITVz9n9kAINo`c}Y3$g-gkY@sEeTMZ)wPn^G1Cx8)h0fGNrlDJH`S"
    "_0^JldZgPrCw=4upr)L(-xx)w)=4XDx0EhQ3Pc(z@5s9IP?JkF35Kd<0jY+Kd=LEPcC#UsQl+m(^xI+44iSKt-xG"
    "1adeGR^tjkHy7_`f*g4obchgGciiS48N#;1#0lDDuzD{*mxjJUay^}`dpgi`uMt6F%Hht7OrYcg_+0^mr;!0C*OL"
    "lu8A<Y;82T55YD>w>PqorkK#2jK(@B#6K8~eA*BbD=UE<_(3<9;gH|c_r<mod*&SN)F7QroT01Brq(^gq#H6uAA*"
    "X2lxguN$=78FD;7PJPqK3!!2RtO5$huF8En+M9@{niLZv$h~F`F5`RDWw$~x&xtN0n<zq6mIn1F0sK`I=l46(T0("
    "Wk<S@&8*h1wtg|_pUk-Yo+mpgEOY&uL`}vJ=F4OXIk)QeAIF}o4TC}V4728So+t07)&sNQ_rJIfKeFE&|n?jWNEt"
    "Chq=Sw<=gJe$)A>02ow~qS?>LOQ(puZ7sK-gZ55uZ{0eV$5bxxpo;hQ8$B3b^I`S6bknh?b>@`qjQss|}CUk%&bE"
    "wn9ps1I^0$bs6q}o{FqE;U4S-(k@ObG*4&hT%@-sjOQi^ns$goa<K$toto$v?*>#uwrj@l)!bl<TROFXxqxGge|~"
    "jzym$OBll_C^@r%==<A2fGjYja7SL5T8gOk(op|o(h2GUr$=IDnscsY5s_hLMGb@cM!#laZOTbvuR^ReMsWO%s|@"
    "47+*$BLe8Ex~}~%Z#kdhKAt4D2~?bY@S~rq>P=Pr7JtIykS}rE07ZDGJsAeiP>|EReNgtLkzMi^<f-TS_%%E@Gi$"
    "%0{+CwESCc1#<1SjZ;|ma&_zKwD@K~qcR}6p)WKtPT97k)i9u)fk_vVv_xe$Mi|#;RQL%iaADyo<l>nRz1;oyrcw"
    "fm&LYfzBibMf>6v`5#g>nJiS{2Qdh-LEXcziNG{@Zwea&$PMEktJ&*gXz3aUf-Vy(Io-Kz#G-XWy|Z8w^5Z5DyfB"
    "nD#jZK4||!oPWal9vJ$NSq$KPpsIYxyy1xNBj}TVf~1(*g;P3E=qZRnraggp5(tsopreT#KvGYM-LnO4z$X}eFqx"
    "3`mCf@HlgU($8DmYPXQVi7)<iSFC+%Odn~M2-$xz{l11SgrTAH$q*FI|i>+ry(GE)(eU~+;7H6zvTjG-z%<cj1m9"
    "Si_Na-m&3q$ixPgFXp`^ZZv8>I!Eo$QG+&b8%^~S14T5_AvRcU?v$tAdD>~9cM^h77Ls}rf*p{cW|&D=vPXAvoF#"
    "ku_zr2{rTS^0dsD0g9L6)kCju#4-sK)Y?r65g$1QS$-67j9KF0H<|D#KNLVkDC2+g87wk<y2>f#AXqbgn<xK-YT%"
    "@b{0?5GJLXzdM5`?`O&p=bXqkf@Id~=H@23eF~RiJu_?AM_RF3V*+VtDs};>bWPL=YFGom^qbh`vg3=kQ1&p)rM^"
    "p^%~9tflcmfG*Z|<ivN=C}-J)s!mFA%vo4{T8i}51dmH(Gp)nMJ_}~KqP*}<c_mY^(ugI(n8HTfXk!O`S9w1)9rP"
    "O)41LXQY1q{q3TfL==v{hPlp@f@H^%J=kyu<=yS_YU-N<Ll-<70?DB)pSAC<Qc##h&CgY#`@meRE5a)e>o$5c=s0"
    "4b|j(r#_w6Ve`0EWpq+8P6dae`_lgTmaw#V1lNLrdBAlQebKw8?y`KVWY54clRzc7zF?rG7K8c2>+Cx6){NjXDr}"
    "Z=3ZL?hwK#4@u{a&axNY>UGw~0Pi{oPo(XWbi~2xB#!QZ>%mq5Rm1-DX5h%X&B+uj42MUP2wAL7TcpTb^VxTjRtB"
    "y2XN)W2qoWiS0`%!(x2p;=45{hx&3BTVci6>@<+!*~R=_oR}C#=fFaYV)4I<Oli>!K4qv>T<ad2bp7Y*vY8{pS*E"
    "h0<#FXs@x^7Kog$$14fS<+_C^qGkEdpb4?sCC(9g=-oC3{(ayQPngal-R%)DYB(1?%vQi}LGd~N8Q0wNo)~g^Lp0"
    "j@o8W=NV3bPl6FJT<I4$ISu_(?+oqdE9&bpVE*)6e03|%YTuHzcBt#;et2a&L`#CvS7`<yRjRMNUwi94_SsGskD7"
    "{9LhGBISFEyh2~o_v-3BAVj#NA(PyEYs`q5{lhp|D`1FPQ6oyeUN}@W6PJAr5X$hs>R5q&{hiwYV}ZsvV4JVg=A$"
    "Di=2MQ;bVlWT5<Nyc&Mwq6fkTkPTp7p{but<0+!y*7uk|*r3L9^H-)MZ(!10Y%*ffrjENmH+<A$NM7&<U{E(M9Y@"
    ">CdN#0OE#jwL@0wo1yEVBNc%T1vZ(SLreEu8q0S1TmJli2=-7KY8zphNvX^gSbSZqC8geAwQ#M!lE1`VPPKk@LpR"
    "ANhs^Yu5r+($zf?65(xD@Jq2c)zvTIMaH~C-)OjagZbH`Y0~lfDXrX%Hjg;F^_~}~JK8ourygMViU4<QJ6sDd-7i"
    "@4uD1@4#;GN&#1%K;i%Hp-?Hhk{2KyYVM%M72H|pqD^eDqN2KpzP`QB^PL?;OAulOy|@j>wh1uBqTIH5u<mJ58w?"
    "piVY=z1u#=WZgTvi^AV`fwlKkdqfjuf}ZshEHeKK9TJLGPHLm(e_LPO4#h<djgKtV;-5ud*(k8Y<K}%p1oHK%PkI"
    "6sfZc_5n>(Z7zL7FH(2B9n`4c5_2zQU8rHn$8<H^{tyhA`*ytReao_jQ&pn8U*EQ~|kZ^Do<gA_i^Gnc`f;6K)YX"
    "gld@})Lo4yn9nzCfLFrDwW0wM%cn)Q&cdbFt!q?mHZ8dRCi})q(@zVK=w7a|Trzh6S6$!}UCl9>^Oj31PN~vXs^Y"
    "PY)V0+|?XAp-r2{L_XCP0lG+tFG%C~x%f!Li<<@##nj5x>eeiL*h1_W_k30xSc~pujdsakSQG`v1=4lJL^MEE5Pl"
    "irfg$C<1<$UPar?j-<Z6%}7w1^kRT1y}l;l%+Uf9!EmvdsP3{1*Ns3f@!mM{3RE$7*86@>6flYXuQ5&309e2Tcuj"
    "630Olxi7;dt_q+qROEoo$3pX)W3l``o%^oFR$80yNi%DS_p=g^W$Azu?+QIn~+m^M-7UdGUAa%W7KWR+T4Jfy>WI"
    "GS%JVwlB>fSKb;;XX7_kY%4X2*V!m=|q#;(Rs-we=VzS*)*0l9OmvG@c61tv=IVfdxm)Cjt&Y9BZ9!t#8#+<p(2P"
    "pab<J0kr)A7FW2mq%dtjdugQm0ab{Y<XtGm`E+5V8|=k08L|DQ4j`edK03->gK1$ivEqp1P(CSyf}h68%f(;-kOh"
    "CQ-@JNq<2zA}xSK_gV3)>oA%k&1H6pf5Xw7+k$(Ahu%>6hJh)ZpDk*a3PffGy<W`yc%<dRsd!e1$Bd<o=5jK8zP&"
    "SeIasZ<V{o0#B>=+bN}I$svUSI{rwCa(jyA>Q=9?K(f=XTZy85rN^D^kJYU>Z(iko~om0V1XEbEyOt*TZjp|O7>a"
    "|JcXb45|%rQFS!;L&u!_kVP5?jYE!;L<Cv8MRK%s|qUbL@%waUd?V`kytj0EWdD)^<|iA7p%p^8EL9#%;&AYNpP+"
    "0S0)M$tPsP9=NuGwhkM<zMypj`qD?*OKSc5@;u*I6_1*<)uveNia>P0E@&v3{<~3mPo%~OkjQmwg7Sc<NmtM2y;C"
    "CavC;GbPBI^cAUd>Dko|*Kc3He?H(zLX4V>I`EICs0zh=L1di$%xr*p*JDusG_x+sN{@DT0kNvJXAmg^~W-lL1Hk"
    "|DFvx@`DG>wA;Fam}X<?Mi#g`^C?DZnXun`YT<s4%=?ol9UW6nyO{w}$2VV*1LVZUu|`*&C)cdP8@^jR@Ddkn2zp"
    "P|&gK9a((diBN`^o;j8ESiW_4{61BF?Q2LE2_-K++>o5Iw_Vi1@kna4pVuj@-w84g765?6Mw=>p6?uB_~tF1ZRq*"
    "~;{!XCp5$t)Wi|m_{v*UAt#7wn$DQE??vl1D#zKMX5cba|tz}qmHb?W@#ZG#`$DOB*gThBnZv1XwCNE4&7l;5S}8"
    "9fl7Eua&;t$UPAk4fG)_aPwyFnG%>;j`*B#1NuJDLbp;#MIJq@O7}~S?$+X^&=qwZ4#U?@TeLVi@^~rcY2uI4{2g"
    "w?<VS-D!QbjSwnRdhR%P8aMOximHI<ITiiL8H4B9?v{-h|vCHSW2ex(z2T8PTy2>e9w^OoGgb$(k+K`Fg_!U&3!K"
    "24T9cOi8-DEj0<I6a`EI*A|V%7G-OZznUtNE^HY8DjZ(NlbG1BXb|vFVk<FQRn}Y?hz(VI(4I~7BT}$vN#8F8N<*"
    "{JlnD$Z+@PJ|(`2gAhpDqCq)&z<9?>8D;yTDUvj{MpO%jcDjl|6b>u6xJ<YXghhk}4orVKF$dteBpfsx*xqp(NP="
    "S4K1M@$vipc^{keI|e?sco~wO|(-`jP1#i03knhy2LhaF7w%C#07<zRZns~I?fAJm~euV4wWMh1M27+wI1spxAB1"
    "Um-s>DT=~Z!QderTc%q9e8q5(S&aWc?rXoaxNN?3Tjw!nrmjM!S_>Q#C7aInBtAzD&yy1RemRG`0(wT-Gdj`S&g!"
    "w()UL}zLD)DuC!3h(t*;(iiawjU1Xm%h(D1a@ft3&dfoRbQ&buHyco@TDnl6@iWxF~P6tpeH5Sybwg6>AQxE34J2"
    "xO&#t?oqhcOPr+8tF2>ylz)G>x@!);>1BcQ-CIUZC}`lF!)iX;uO4^{66La-Io3lxcn`5658r3m^+Qk$3tFr@4og"
    "!AFD_Ffp_b2}$2Udr+$&do7v~bb<6MmMVe;`|FL@|=?y3*g7rfiO+ZxB)$TCl=8Hp|F0M;~a6eQ=>eOp=^9z@4}O"
    "Izc{LGQn7J9+&Qg>jRQ@wy}E%Y0f#ZlbhmE+X@s(utyw;lwfH=A?w0x7!48slkqrZ7K7S<R&a+eLSx`FnbZ+f}9+"
    "uB~)dkW6<@%ynIwfY+QG{m}L3*i8TK9!NHQm#X4secuB&v-p88-Bl4ZxJE|^3q_Voz#<S8OaSQ3Y{RxO)vaXsE9M"
    "lx>$OmRen&33sGoVaj(X?ruYPgv17+7g@bLONCESJ%FYt4<kH~JgSU0Oob=CY-sIFfD~1$eI}y{lq7YW*%_G48+o"
    "i0nnyKgHUCjMsQpo!}*O7!T#B&av`!v6)>Cs)en1KT}GA>d!^^^1Msc;-*l|=<ub{{bjXmsOeF@Tcm8k+vS71{|8"
    "wfOA!"
)
course_bytes = zlib.decompress(base64.b85decode(COURSE_ARCHIVE))
if (
    hashlib.sha256(course_bytes).hexdigest()
    != "8a32db0dd1c6fe29efc0f2201509fd602f5a1692d275e1a3a75fefaf19e2fc7b"
):
    raise ValueError("Embedded course files failed their integrity check")
course_files = json.loads(course_bytes)
if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd().resolve()
if "COURSE_RUNTIME_DIRECTORY" not in globals():
    COURSE_RUNTIME_DIRECTORY = tempfile.TemporaryDirectory(prefix="lucy-practical-runtime-")
COURSE_ROOT = Path(COURSE_RUNTIME_DIRECTORY.name)
for course_relative, course_content in course_files.items():
    course_target = COURSE_ROOT / course_relative
    if not course_target.resolve().is_relative_to(COURSE_ROOT.resolve()):
        raise ValueError("Invalid embedded relative path")
    course_target.parent.mkdir(parents=True, exist_ok=True)
    course_target.write_text(course_content, encoding="utf-8")
for course_import_path in (COURSE_ROOT, COURSE_ROOT / "src"):
    if str(course_import_path) not in sys.path:
        sys.path.insert(0, str(course_import_path))
# Reviewed local subprocesses import the same supplied modules. Colab installs no
# package, so register the scratch runtime the way an editable install does: a .pth
# file in the interpreter's site-packages, or in the user site when that is read-only.
course_pth = str(COURSE_ROOT / "src") + "\n" + str(COURSE_ROOT) + "\n"
for course_site in (sysconfig.get_paths()["purelib"], site.getusersitepackages()):
    try:
        Path(course_site).mkdir(parents=True, exist_ok=True)
        (Path(course_site) / "lucy-course-runtime.pth").write_text(course_pth)
        break
    except OSError:
        continue
os.environ["PYTHONPATH"] = os.pathsep.join(
    [str(COURSE_ROOT / "src"), str(COURSE_ROOT)]
    + [entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry]
)
COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch15-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
ROOT = COURSE_ROOT
print("Python", sys.version.split()[0], "Pydantic", pydantic.__version__)
print("Offline teaching files ready:", len(course_files))
print("Save your work here:", COURSE_WORK)
```

</details>



## Commit to a prediction before the examples


```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write the expected behavior before running the worked example.",
    "reason": "Name the input and rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Reading the Python vocabulary used in this notebook

You need basic assignments, `if`, loops, functions, lists and dictionaries. The less familiar
features used by the supplied code are introduced here. A **library** is reusable code that
Python can import. The **standard library** ships with Python; Pydantic is an additional package.
An import makes a name available, but does not mean that you have completed the exercise.

**JSON** is text for exchanging structured values. A Python dictionary is an in-memory object;
the JSON representation is a string. Use `json.dumps` to encode and `json.loads` to decode.
Decoding proves that text has valid JSON syntax, not that its fields match our business contract.
Predict which of the following two decoded objects could describe a stock count.

```python tags=["foundation", "worked-example"]
import json

intro_data = {"sku": "MANGO", "count": 3}
intro_text = json.dumps(intro_data, sort_keys=True)
print(type(intro_data).__name__, type(intro_text).__name__, intro_text)
print(json.loads(intro_text))
print("Also valid JSON:", json.loads('["not", "a", "stock", "record"]'))
assert json.loads(intro_text) == intro_data
```

The first result is a dictionary; the second is a list. Before indexing a decoded object,
check the shape that your function promises to accept. An **exception** interrupts the normal
path. `raise ValueError(...)` refuses an invalid value; `try`/`except` lets a caller inspect that
expected refusal. Catch the expected class, rather than turning every programming error into
apparent success. `finally` runs cleanup even when an earlier operation raises.

An **annotation**, such as `count: int`, documents the expected type. It does not by itself
enforce the type at runtime. A **class** defines a kind of object; an instance holds one object's
data. `@dataclass` asks Python to generate routine construction and comparison methods from
annotated fields. `frozen=True` prevents ordinary reassignment of the instance's fields; it does
not make every object nested inside those fields immutable. A **method** is a function attached
to a class; `self` refers to the instance receiving the call.

```python tags=["foundation", "worked-example"]
from dataclasses import dataclass


@dataclass(frozen=True)
class IntroObservation:
    operation: str
    count: int


intro_observation = IntroObservation("count-mango", 3)
print(intro_observation.operation, intro_observation.count)
assert intro_observation == IntroObservation("count-mango", 3)
```

A **callback** is a function passed to another function. This is how the classroom harness
invokes *your* implementation. The argument `candidate` below is a function object; parentheses
perform the call. Predict the two answers before execution, then trace the result to the callback.

```python tags=["foundation", "worked-example"]
def intro_apply(candidate, value):
    return {"input": value, "observed": candidate(value)}


def intro_double(value):
    return value * 2


print(intro_apply(intro_double, 3))
print(intro_apply(lambda value: value + 2, 3))
assert intro_apply(intro_double, 3)["observed"] == 6
```

`lambda value: value + 2` is a small anonymous function. A **closure** is a function that retains
access to values from its surrounding scope. It can bind a tool to a shop snapshot. A shallow
copy duplicates only the outer container; `copy.deepcopy` also copies nested containers used
in these fixtures. A **set** stores distinct values; `required <= allowed` asks whether every
required item is allowed. `frozenset` is the corresponding immutable set. A tuple groups ordered
values; `(value,)` is a one-item tuple, including the comma.

**Paths and cleanup.** `Path` represents a filesystem location. `path / "file.json"` constructs
a child path; `read_text` and `write_text` read and write text. A context manager, used with
`with`, manages entry and exit. A temporary-directory context removes its contents on exit.
Save your submission outside temporary runtime directories. Reopening a file is different from
reusing a Python variable: the former tests retained bytes, while the latter only tests this kernel.

```python tags=["foundation", "worked-example"]
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as intro_folder:
    intro_path = Path(intro_folder) / "observation.json"
    intro_path.write_text(json.dumps(intro_data), encoding="utf-8")
    intro_reopened = json.loads(intro_path.read_text(encoding="utf-8"))
    assert intro_reopened == intro_data
    print("Read from a file:", intro_reopened)
```

**Retrieval check:** explain JSON versus a dictionary, annotation versus validation, class versus
instance, and defining a callback versus invoking it. Change the callback above so an incorrect
implementation visibly changes the observed output. This distinction will matter when grading
your connected work. Reference: Python's [JSON](https://docs.python.org/3.12/library/json.html),
[dataclasses](https://docs.python.org/3.12/library/dataclasses.html), and
[pathlib](https://docs.python.org/3.12/library/pathlib.html) documentation.


### Pydantic: turn an input dictionary into a checked object

Pydantic is an additional Python library for validating data. Its **model** is a class describing
fields, not a neural network. Inherit from `BaseModel`, declare annotated fields, then call
`model_validate` on incoming data. A field without a default is required. A field with a default
can be omitted. The result is an instance whose values you read with dot notation.

```python tags=["foundation", "worked-example"]
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class IntroCourseRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=1000)
    note: str = ""


intro_request = IntroCourseRequest.model_validate({"name": "mango", "quantity": 4})
print(intro_request.name, intro_request.quantity, repr(intro_request.note))
assert intro_request.note == ""
```

The annotation says the field's type. `Field` supplies constraints: `gt=0` means greater than
zero, `le=1000` means at most 1000, and `min_length=1` excludes an empty name. `ConfigDict` sets
model-wide behavior. `strict=True` rejects conversions for this integer field, including `"4"`,
`4.0` and `True`; `extra="forbid"` rejects undeclared keys. Pydantic can otherwise convert some
compatible inputs, so choose this boundary deliberately rather than assuming every accepted
input arrived in the expected type.

Predict which rule refuses each payload. `ValidationError` reports a failed contract. Its
`errors()` entries contain `loc`, the field location, and `type`, the failure category. Catching
that expected exception lets the notebook inspect the failure and continue.

```python tags=["foundation", "worked-example"]
intro_bad_requests = [
    {"name": "mango", "quantity": "4"},
    {"name": "mango", "quantity": True},
    {"name": "", "quantity": 4},
    {"name": "mango", "quantity": 0},
    {"name": "mango", "quantity": 4, "approved": True},
    {"quantity": 4},
]
for intro_bad_request in intro_bad_requests:
    try:
        IntroCourseRequest.model_validate(intro_bad_request)
    except ValidationError as intro_error:
        print([(item["loc"], item["type"]) for item in intro_error.errors(include_input=False)])
    else:
        raise AssertionError("An invalid input crossed the declared contract")
```

Use `model_dump()` for a Python dictionary, `model_dump_json()` for JSON text, and
`model_validate_json()` to parse and validate JSON. `model_json_schema()` describes the contract;
it is neither an instance's current values nor an invocation of the business handler.

```python tags=["foundation", "worked-example"]
intro_serialized = intro_request.model_dump_json()
intro_schema = IntroCourseRequest.model_json_schema()
assert IntroCourseRequest.model_validate_json(intro_serialized) == intro_request
print("Actual values:", intro_request.model_dump())
print("Quantity contract:", intro_schema["properties"]["quantity"])
assert intro_schema["properties"]["quantity"]["exclusiveMinimum"] == 0
```

Four is valid input to this schema even if the shop needs six. Pydantic checks the declared
shape and constraints; the handler still needs authoritative stock, price and permission.
Ordinary assignments to an existing instance are not automatically revalidated unless configured
for assignment validation. This lesson validates new input at the boundary and uses the resulting
values. Explain these limits before relying on a model object in a transaction or tool call.

Chapter 2's full introduction expands this pattern with a separate data-repair checkpoint.
This notebook contains the required pattern here so prior Pydantic experience is not needed.
References: [models](https://docs.pydantic.dev/latest/concepts/models/),
[fields](https://docs.pydantic.dev/latest/concepts/fields/), and
[strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/).


## Exposing a tool and permitting a call are separate operations

A registry lists implemented tools. An allowlist names the subset one worker may use. A hostile
instruction might ask a stock-reading worker to purchase goods. The instruction can change what
the model requests; it must not change the worker's deterministic permissions. A **trust boundary**
separates data we interpret from authority we accept. Retrieved text and tool descriptions are
data, even when they contain imperative sentences.

### Start with a handler counter

If a dispatcher returns “not allowed” after executing a handler, the error message is reassuring
but the effect has already happened. Record a local event inside the handler so we can observe
whether it ran. Predict both the result and event list for a registered but forbidden tool.

```python tags=["foundation", "worked-example"]
intro_handler_events = []
intro_registry = {"stock": lambda: intro_handler_events.append("stock-ran") or 6}
intro_allowlist = set()


def intro_dispatch(name):
    if name not in intro_registry or name not in intro_allowlist:
        return {"ok": False, "error": "not_allowed"}
    return {"ok": True, "value": intro_registry[name]()}


assert intro_dispatch("stock")["ok"] is False
assert intro_handler_events == []
intro_allowlist.add("stock")
assert intro_dispatch("stock") == {"ok": True, "value": 6}
assert intro_handler_events == ["stock-ran"]
print(intro_handler_events)
```

This is local Python admission, not a sandbox. A **process** has its own interpreter and memory;
starting a subprocess does not automatically remove filesystem or network privileges. **OS
containment** requires operating-system controls under a stated threat model. The core notebook
proves mediation and effect ordering; the separate container experiment is needed for claims
about operating-system enforcement.

### A protocol describes messages across a boundary

**MCP**, the Model Context Protocol, defines how clients and servers exchange capabilities and
tool requests. This book uses a small pinned protocol implementation rather than assuming an
MCP SDK. **JSON-RPC** supplies request/response envelopes with method names and correlation IDs.
A **transport** carries those bytes; standard input/output is one possible transport. A request
ID correlates a reply to a request. It is not automatically the durable business-operation ID
that protects a supplier purchase from duplication.

```python tags=["foundation", "worked-example"]
import json

intro_rpc_request = {
    "jsonrpc": "2.0",
    "id": 17,
    "method": "tools/call",
    "params": {"name": "list_stock", "arguments": {}},
}
intro_rpc_reply = {"jsonrpc": "2.0", "id": 17, "result": {"count": 3}}
intro_wire = json.dumps(intro_rpc_request)
assert json.loads(intro_wire)["params"]["name"] == "list_stock"
assert intro_rpc_reply["id"] == intro_rpc_request["id"]
print("Correlated request and reply:", intro_rpc_request["id"], intro_rpc_reply["id"])
```

These two objects illustrate correlation, not a complete MCP handshake. A real session also
has initialization and capability rules. The notebook's frozen runtime supplies those mechanics
where the chapter probe uses them. You still inspect the tool name, arguments, permission and
handler observation that matter to the exercise. Reference: the pinned
[MCP 2025-06-18 basic protocol description](https://modelcontextprotocol.io/specification/2025-06-18/basic/index).

### Bounds have different positions in the execution path

Argument validation belongs before the handler. A consequential tool needs an authority guard
before the handler. The serialized result's byte length can be known only after a result exists.
If that final size check refuses output, it does not roll back an earlier side effect. This is
a limitation of that boundary, not a reason to pretend the effect never happened.

Errors returned to a caller should describe the refusal without unnecessarily echoing raw
validation inputs. The actual dispatcher catches declared operational exceptions and returns
bounded observations. An unrelated programming exception must not be counted as proof that
the correct permission check ran.

The construction task implements registry lookup, allowlist membership, strict arguments,
authority guard, handler invocation and bounded JSON output in order. The failure task removes
the allowlist condition. The transfer includes an unseen tool, an allowed read, a denied known
read, a consequential call and an oversized result. Draw the event order for each before coding,
and state which claims still require a supported container or host experiment.


## Choose an explicit starting point for this independent notebook

This Unit B runs without Unit A. By default it prepares a **supplied reference starting point**
and labels its provenance. It is not evidence that you built Unit A. To investigate your own
successful implementation, set `LEARNER_HANDOFF` to its saved path before running the cell.
An invalid selected file refuses; it is never silently replaced with the reference.

`SourceTask` supplies copied-source execution and handoff validation; `RuntimeLab` supplies the
controlled failure experiment. Their public operations are introduced beside the main exercise.
The artifact stores identity and observations; no variables from another kernel are required.


```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

<details><summary>Prepare and validate the supplied starting artifact</summary>


```python tags=["setup", "independent-reference-start"]
import json
import runpy
import shutil
import textwrap
from pathlib import Path

COURSE_INPUT = COURSE_WORK / "ch15-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    source_task_class = runpy.run_path(
        str(COURSE_ROOT / "book/always_on/exercises/source_tasks_v1.py")
    )["SourceTask"]
    reference_task = source_task_class(COURSE_ROOT, 11)
    try:
        reference_task.install(textwrap.dedent(reference_task.fragment))
        reference_observation = reference_task.visible("SUPPLIED_REFERENCE_START")
        if reference_observation["status"] != "PASS":
            raise RuntimeError("The supplied starting point did not pass its connection check")
        reference_task.save(COURSE_INPUT, reference_observation)
    finally:
        reference_task.close()
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
print("The core task below validates the selected artifact before using it.")
```

</details>



## Understand the supplied execution interface

The course runtime is provided so your implementation can be connected to real callers and
storage. `SourceTask(ROOT, chapter)` makes a private copy. `install(source)` replaces only the
declared function; `visible()` invokes the real chapter probe; `save(path, result)` retains a
successful implementation and its evidence. `load(path)` checks the saved identities and hashes.
`inject_failure()` changes the declared boundary; `repair(fragment)` replaces that broken fragment.
`close()` removes the scratch copy after you retain evidence. These methods are supplied harness
operations, not additional packages you must discover or install.

`RuntimeLab` provides the same copied-source failure experiment without the complete-function
construction layer. Its `run` method records exit status, observations and the compared expectation.
A subprocess log from an unfinished learner implementation is feedback about that implementation;
it is not a successful connection. A syntax error in the notebook cell itself is a separate issue
to fix. The task below names which interface it uses.

For direct-function units, the visible driver calls your callback without installing a source
string. In either case, trace where your code is invoked. Supplied fixtures, database wrappers and
replay models are labeled infrastructure; your own implementation and changed-case explanation
are the evidence of learning.


<!-- #region -->
## Main practical: construct, connect and challenge



A known tool can still be unavailable to this particular worker. This time you begin with your Unit A implementation and its saved evidence. Private shop data can leave a registered handler despite Lucy withholding permission to use it.

## Verify the handoff

The starting-point cell has selected the Unit A artifact explicitly. A selected learner handoff must validate; the default reference start is labeled separately. Run the setup and keep the runtime and implementation hashes in your submission.
<!-- #endregion -->

```python tags=["setup", "handoff-consumer"]
import json
import os
import runpy
from pathlib import Path

ROOT = COURSE_ROOT

SourceTask = runpy.run_path(str(ROOT / "book/always_on/exercises/source_tasks_v1.py"))["SourceTask"]
REFERENCE_LESSON = 11
HANDOFF = Path("ch15-unit-a-handoff-v1.json")
handoff_status = "MISSING"
if HANDOFF.is_file():
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        handoff = task.load(HANDOFF)
        handoff_status = "VERIFIED"
        print("IMPLEMENTATION", handoff["implementation_sha256"])
    finally:
        task.close()
print("UNIT_A_HANDOFF", handoff_status)
```

## Reproduce and diagnose

Predict the consequence of this injected boundary before executing it:

```text
if tool is None:
```

The controlled mutation changes the same implementation you submitted. It refuses if the declared mutation boundary no longer occurs exactly once; inspect an alternative implementation with the instructor before adapting the experiment.

```python tags=["failure-experiment"]
baseline = broken = None
if handoff_status == "VERIFIED":
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        task.load(HANDOFF)
        baseline = task.visible("YOUR_BASELINE")
        if baseline["status"] != "PASS":
            raise ValueError("Saved Unit A code no longer satisfies the visible contract")
        task.inject_failure()
        broken = task.run("INJECTED_FAILURE", expected=task.spec["expected_broken"])
        print("BEFORE", baseline["observation"])
        print("AFTER", broken["observation"])
    finally:
        task.close()
else:
    print("HANDOFF_REQUIRED: complete Unit A before performing Unit B")
```

State a diagnosis using those two observations. Name a test that would prove your diagnosis wrong. Install the method in the real Dispatcher and observe handler invocation counters, not just returned text.

## Repair the boundary

Return the complete replacement for the injected fragment. Do not edit the oracle or print a desired observation. Repair the actual source. The starter keeps the defect so the learner outcome remains incomplete.

```python tags=["exercise", "learner-owned"]
def repair_fragment():
    return "if tool is None or call.name not in self.allowed:"
```

<details><summary>Hint 1 — the consequence</summary>

Private shop data can leave a registered handler despite Lucy withholding permission to use it.

</details>

<details><summary>Hint 2 — the evidence</summary>

Compare the two observations, then trace the changed field to `invoke` in `src/sovereign_agent/tool_dispatch.py`. Distinguish a schema refusal from a business-rule or authority refusal.

</details>

<details><summary>Hint 3 — the design</summary>

Check membership before argument validation, require a guard for consequential tools, run it before the handler and enforce encoded output size.

</details>

```python tags=["integration", "learner-path"]
def connect_repair(fragment):
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        task.load(HANDOFF)
        task.inject_failure()
        task.repair(fragment)
        return task.visible("YOUR_REPAIR")
    finally:
        task.close()


repair_result = None
if handoff_status == "VERIFIED":
    repair_result = connect_repair(repair_fragment())
    print("REPAIR", repair_result["status"], repair_result["observation"])
else:
    print("REPAIR_NOT_ATTEMPTED: missing Unit A evidence")
```

## Transfer under a changed constraint

Use an unseen tool name, a valid allowed read, a denied registered read, a consequential call and oversized output.

Create a fresh task, load your handoff, inject the defect and apply your repair. Then change only the copied probe to exercise the new condition. Keep the actual observation and a prediction written beforehand. Explain why a visible-case lookup or a blanket refusal could pass the original example but fail this transfer.

The instructor's holdout applies your repair to a new copied runtime and checks both the positive case and the missing protection. An exact exception or changed state must cause a failure; no broad error is accepted as successful refusal.

## Exit ticket

Submit the original handoff, baseline and broken observations, repair, transfer probe and results. State what Lucy would experience before and after the fix. Identify the guarantee that still requires separate evidence: Dispatcher admission is not OS or network containment; container execution remains a separate chapter experiment.

```python tags=["exercise-report"]
passed = repair_result is not None and repair_result["status"] == "PASS"
exercise_report = {
    "unit": "ch15-b",
    "attempted": int(repair_result is not None),
    "completed": int(passed),
    "failed": int(repair_result is not None and not passed),
    "skipped": int(repair_result is None),
    "connection": "PASS" if passed else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: Separate registration, permission and consequential authority

**Allow twenty minutes.** Spend three minutes predicting, ten implementing and tracing, five
on a new case of your own, and two explaining the surviving limitation. This is dedicated work,
not an invitation to run a supplied answer. Both units revisit the same invariant after different
core experiences; in Unit B, attempt this task from memory before consulting Unit A.

Implement transfer_check(name, registered, allowed, consequential, has_authority). Return True only for a name in both registered and allowed and, if consequential is True, with has_authority=True. Inputs are validated names, lists and booleans. The driver records an effect only when your function admits it; compare effects as well as decisions.

Write your expected values before running the table. Keep one accepted case and one refusal.
Your function is passed directly into the driver below. The driver copies inputs and checks
they remain unchanged; it does not replace your implementation with the reference answer.

<details><summary>Hint 1 — identify the authoritative inputs</summary>
Name the source field for each output value. Which input changes while the rule remains the same?
</details>
<details><summary>Hint 2 — choose the boundary cases</summary>
Start with exact empty, exact equality and one value on each side of the boundary where valid.
Do not add a special case for a visible product name or operation identity.
</details>


```python tags=["exercise", "transfer-owned"]
def transfer_check(name, registered, allowed, consequential, has_authority):
    return name in registered and name in allowed and (not consequential or has_authority)
```

```python tags=["assessment", "transfer-invocation"]
import copy
import json

TRANSFER_CASES = [
    ("allowed read", ["stock", ["stock"], ["stock"], False, False], True),
    ("registered forbidden", ["stock", ["stock"], [], False, False], False),
    ("unregistered advertised", ["buy", [], ["buy"], True, True], False),
    ("write lacks authority", ["buy", ["buy"], ["buy"], True, False], False),
]


def same_transfer_value(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            same_transfer_value(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            same_transfer_value(a, e) for a, e in zip(actual, expected, strict=True)
        )
    return actual == expected


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        before = copy.deepcopy(supplied)
        raised = None
        try:
            actual = candidate(*supplied)
        except NotImplementedError:
            raised = "NotImplementedError"
            actual = {"unfinished": True}
        except Exception as error:
            raised = type(error).__name__
            actual = {"raises": raised}
        expects_error = isinstance(expected, dict) and set(expected) == {"raises"}
        correct = (
            raised == expected["raises"]
            if expects_error
            else (raised is None and same_transfer_value(actual, expected))
        )
        passed = correct and same_transfer_value(supplied, before)
        observations.append(
            {"case": label, "expected": expected, "observed": actual, "passed": passed}
        )
        print("PASS" if passed else "NEEDS_WORK", label, "expected", expected, "observed", actual)
    return observations


transfer_observations = run_transfer(transfer_check, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one new case with an independently calculated expected outcome to `TRANSFER_CASES` and rerun
the driver. Change one condition at a time. Then deliberately replace your candidate with a
constant answer in a temporary copy and show a case that rejects it. Restore your implementation.
Explain why that counterexample is stronger than repeating the original example with a new name.

Without viewing the worked example, write the invariant in words and trace one observed value
back to its input. Identify which part is a local fixture result and which claim would need a
live provider, host or external-system observation. Keep a first attempt even if you used a hint.



### Observe the effect boundary
The handler event is recorded only after your decision. Predict the event list for the refused write followed by the permitted read.


```python tags=["integration", "transfer-connection"]
if TRANSFER_PASSED:
    transfer_effects = []

    def mediated_transfer(name, allowed, consequential, authority):
        if not transfer_check(name, ["stock", "buy"], allowed, consequential, authority):
            return "REFUSED"
        transfer_effects.append(name)
        return "RAN"

    assert mediated_transfer("buy", ["buy"], True, False) == "REFUSED"
    assert transfer_effects == []
    assert mediated_transfer("stock", ["stock"], False, False) == "RAN"
    assert transfer_effects == ["stock"]
    print("Observed handler events:", transfer_effects)
else:
    print("Finish the transfer guard before inspecting its effect boundary.")
```

## Instructor explanation and additional transfer cases

The permission decision must precede invocation. A known name is not sufficient authority, and an allowed name without an implementation is not callable. OS containment remains a different boundary.

Ask for the learner's first prediction and attempt before revealing this version. Passing these
cases verifies behavior on these inputs; it does not establish independent student mastery.
The original core holdouts also run against the connected implementation below.


```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("authorized write", ["buy", ["buy"], ["buy"], True, True], True),
    ("new allowed tool", ["quote", ["stock", "quote"], ["quote"], False, False], True),
]
instructor_transfer = run_transfer(transfer_check, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_transfer)
```

```python tags=["instructor-check", "core-holdout"]
# Instructor holdout appended to a submitted Chapter 12 Unit B.

# ruff: noqa: F821
import json

task = SourceTask(ROOT, REFERENCE_LESSON)
try:
    task.load(HANDOFF)
    task.inject_failure()
    task.repair(repair_fragment())
    outcome = task.transfer(ROOT / "book/always_on/exercises/ch11/holdouts/runtime-transfer-v1.py")
    assert outcome["status"] == "PASS", outcome
finally:
    task.close()
print("HOLDOUT_RESULT=" + json.dumps({"unit": "ch15-b", "status": "PASSED"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill the prediction notes and your explanation before saving. Include the exact observed value,
the input or retained row that caused it, your code's invocation point, one failed hypothesis,
and the strongest claim the evidence still cannot support. A completed code cell alone does not
earn explanation credit. Do not label reference-start behavior as your own Unit A construction.

Keep this edited notebook, the Markdown if used for notes, saved handoff files, and the JSON record
below. Your work folder survives scratch cleanup and can be reopened in a new kernel. An instructor
can ask for an unseen case after the visible checks; keep your implementation general.


```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch15-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch15-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch15-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "instructor",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.

<!-- #endregion -->
