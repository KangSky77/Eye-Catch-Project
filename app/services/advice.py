"""
AI 소견 3줄 — '고르기' 방식 (settings.opinion_mode == "choice")
================================================================
왜 이렇게 바꿨나 (2026-09-27 측정):
    예전에는 Gemma가 조언 문장을 직접 썼다. 작은 모델(e2b)도 큰 모델(e4b)도 20번 중 3번꼴로
    문진 사실을 잘못 옮겼다("2년 내 검진 없음" → "지난 검진 기록에 따라", 묻지 않은 금연 조언 등).
    프롬프트와 안전 필터로 막을 수 있는 건 '이미 알고 있는 틀린 표현'뿐이었다.

구조:
    1) 문진 사실(flag_codes 등)로 '이 사람에게 해당하는 선택지'를 코드가 먼저 추린다.
       예: 당뇨가 아니면 혈당 조언은 선택지에 아예 없다.
    2) AI는 JSON 스키마(enum)로 그 선택지 중에서 '고르기'만 한다 — 목록 밖의 값은 낼 수 없다.
    3) 문장은 여기 적힌 검수된 문장(6개 언어)으로 서버가 조립한다.
    그래서 AI가 무엇을 고르든 사실을 뒤집는 문장은 만들어질 수 없다.
    AI의 몫은 '이 사람에게 가장 맞는 조언 고르기'다.

해석·판정·권장 조치는 여전히 프론트 코드가 정한다(app-findings.js, app-assess.js).
응급(red flag)은 이 모듈 전에 llm.py가 고정 문장으로 처리한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

LANGS = ("ko", "en", "es", "fr", "ja", "zh")

# ── 1줄째: 안과에서 받게 될 검사 ────────────────────────────────────────
EXAM_LINE = {
    "ko": "안과에서는 {a}, {b} 같은 검사로 눈 상태를 확인하게 됩니다.",
    "en": "At the eye clinic, your eyes will be checked with tests such as the {a} and the {b}.",
    "es": "En la consulta de oftalmología le revisarán los ojos con pruebas como {a} y {b}.",
    "fr": "Chez l’ophtalmologiste, vos yeux seront examinés par des examens comme {a} et {b}.",
    "ja": "眼科では{a}や{b}などの検査で目の状態を確認します。",
    "zh": "在眼科会通过{a}和{b}等检查了解眼睛的状况。",
}

EXAMS = {
    "slit_lamp": {
        "desc": "slit-lamp microscope exam of the cornea and lens (checks lens clouding)",
        "name": {"ko": "세극등 현미경 검사", "en": "slit-lamp exam", "es": "el examen con lámpara de hendidura",
                 "fr": "l’examen à la lampe à fente", "ja": "細隙灯顕微鏡検査", "zh": "裂隙灯检查"},
        "why": {
            "ko": "세극등 현미경 검사는 가는 빛줄기로 각막과 수정체를 확대해 보는 검사로, 수정체가 뿌옇게 변했는지 확인합니다.",
            "en": "A slit-lamp exam uses a thin beam of light and a microscope to look closely at the cornea and lens, including whether the lens has become cloudy.",
            "es": "El examen con lámpara de hendidura usa un haz fino de luz y un microscopio para ver de cerca la córnea y el cristalino, incluso si el cristalino se ha vuelto opaco.",
            "fr": "L’examen à la lampe à fente utilise un fin faisceau lumineux et un microscope pour observer la cornée et le cristallin, notamment s’il est devenu trouble.",
            "ja": "細隙灯顕微鏡検査は細い光と顕微鏡で角膜や水晶体を拡大して見る検査で、水晶体の濁りも確認します。",
            "zh": "裂隙灯检查用细光束和显微镜放大观察角膜和晶状体，包括晶状体是否变得浑浊。",
        },
    },
    "dilated_fundus": {
        "desc": "dilated fundus exam of the retina and optic nerve",
        "name": {"ko": "동공을 넓혀 망막을 보는 안저 검사", "en": "dilated retina (fundus) exam",
                 "es": "el fondo de ojo con dilatación", "fr": "le fond d’œil après dilatation",
                 "ja": "散瞳眼底検査", "zh": "散瞳眼底检查"},
        "why": {
            "ko": "안저 검사는 안약으로 동공을 넓힌 뒤 망막과 시신경을 살펴보는 검사로, 검사 후 몇 시간은 눈이 부시고 가까운 것이 흐릴 수 있어 운전은 피하는 것이 좋습니다.",
            "en": "A dilated fundus exam uses eye drops to widen the pupil so the retina and optic nerve can be checked; for a few hours afterwards light may feel bright and near vision blurry, so avoid driving.",
            "es": "En el fondo de ojo con dilatación se usan gotas para agrandar la pupila y revisar la retina y el nervio óptico; durante unas horas la luz puede molestar y la visión de cerca estar borrosa, así que evite conducir.",
            "fr": "Pour le fond d’œil, des gouttes dilatent la pupille afin d’examiner la rétine et le nerf optique ; pendant quelques heures, la lumière peut éblouir et la vision de près être floue, évitez donc de conduire.",
            "ja": "散瞳眼底検査は目薬で瞳孔を広げて網膜や視神経を調べる検査です。検査後数時間はまぶしく近くが見えにくいため、車の運転は避けましょう。",
            "zh": "散瞳眼底检查会用眼药水放大瞳孔以检查视网膜和视神经；检查后几个小时内可能畏光、看近处模糊，请避免开车。",
        },
    },
    "oct": {
        "desc": "OCT cross-section scan of the retina (macula, diabetic retina changes)",
        "name": {"ko": "망막 단층 촬영(OCT)", "en": "OCT retinal scan", "es": "la tomografía de retina (OCT)",
                 "fr": "la tomographie de la rétine (OCT)", "ja": "網膜の断層撮影（OCT）", "zh": "视网膜断层扫描（OCT）"},
        "why": {
            "ko": "망막 단층 촬영(OCT)은 빛으로 망막의 단면을 찍는 검사로, 아프지 않고 몇 분이면 끝납니다.",
            "en": "An OCT scan uses light to take cross-section images of the retina; it is painless and takes a few minutes.",
            "es": "La OCT toma imágenes en corte de la retina con luz; no duele y dura unos minutos.",
            "fr": "L’OCT prend des images en coupe de la rétine grâce à la lumière ; c’est indolore et cela dure quelques minutes.",
            "ja": "OCTは光で網膜の断面を撮影する検査で、痛みはなく数分で終わります。",
            "zh": "OCT用光拍摄视网膜的断层图像，无痛，几分钟即可完成。",
        },
    },
    "iop": {
        "desc": "eye pressure (intraocular pressure) measurement",
        "name": {"ko": "안압 측정", "en": "eye pressure test", "es": "la medición de la presión ocular",
                 "fr": "la mesure de la pression de l’œil", "ja": "眼圧検査", "zh": "眼压测量"},
        "why": {
            "ko": "안압 측정은 눈 속 압력을 재는 검사로, 공기를 살짝 불거나 안약을 넣은 뒤 짧게 잽니다.",
            "en": "An eye pressure test measures the pressure inside the eye, usually with a quick puff of air or after numbing drops.",
            "es": "La medición de la presión ocular mide la presión dentro del ojo, normalmente con un breve soplo de aire o tras unas gotas anestésicas.",
            "fr": "La mesure de la pression de l’œil se fait en général par un bref souffle d’air ou après des gouttes anesthésiantes.",
            "ja": "眼圧検査は目の中の圧力を測る検査で、空気を軽く当てるか点眼麻酔の後に短時間で測ります。",
            "zh": "眼压测量检测眼内的压力，通常用一股轻微的气流，或滴麻醉眼药水后快速测量。",
        },
    },
    "visual_field": {
        "desc": "visual field test of side vision (glaucoma follow-up)",
        "name": {"ko": "시야 검사", "en": "visual field test", "es": "la campimetría (prueba de campo visual)",
                 "fr": "l’examen du champ visuel", "ja": "視野検査", "zh": "视野检查"},
        "why": {
            "ko": "시야 검사는 한쪽 눈씩 화면에 나타나는 불빛을 보고 버튼을 눌러 보이는 범위를 확인하는 검사입니다.",
            "en": "A visual field test checks how wide you can see by pressing a button when lights appear, one eye at a time.",
            "es": "La campimetría comprueba la amplitud de su visión: pulsará un botón cuando vea aparecer luces, con un ojo cada vez.",
            "fr": "L’examen du champ visuel mesure l’étendue de votre vision : vous appuyez sur un bouton quand des lumières apparaissent, un œil à la fois.",
            "ja": "視野検査は片目ずつ、光が見えたらボタンを押して見える範囲を調べる検査です。",
            "zh": "视野检查每次一只眼睛，看到光点时按下按钮，以确认能看到的范围。",
        },
    },
}

# ── 2줄째: 문진 항목과 이어지는 생활 관리 ─────────────────────────────────
CARE = {
    "glucose": {
        "desc": "blood sugar control (person has diabetes)",
        "line": {
            "ko": "혈당을 꾸준히 관리하면 망막 혈관을 지키는 데 도움이 됩니다.",
            "en": "Keeping your blood sugar well controlled helps protect the small blood vessels in the retina.",
            "es": "Mantener controlada la glucosa en sangre ayuda a proteger los vasos de la retina.",
            "fr": "Garder une glycémie bien contrôlée aide à protéger les petits vaisseaux de la rétine.",
            "ja": "血糖値をきちんと管理すると、網膜の血管を守ることにつながります。",
            "zh": "持续控制好血糖，有助于保护视网膜的血管。",
        },
        "why": {
            "ko": "당뇨가 오래되거나 혈당 조절이 어려우면 망막 혈관이 약해질 수 있어, 혈당 관리는 눈 관리이기도 합니다.",
            "en": "Long-standing or poorly controlled diabetes can weaken the retina's blood vessels, so managing blood sugar is also eye care.",
            "es": "La diabetes de larga duración o mal controlada puede dañar los vasos de la retina, por eso controlar la glucosa también cuida los ojos.",
            "fr": "Un diabète ancien ou mal équilibré peut fragiliser les vaisseaux de la rétine : surveiller la glycémie, c’est aussi prendre soin des yeux.",
            "ja": "糖尿病が長い場合や血糖のコントロールが難しい場合は網膜の血管が傷みやすく、血糖管理は目のケアでもあります。",
            "zh": "糖尿病病程较长或血糖控制不佳时，视网膜血管容易受损，所以控制血糖也是在保护眼睛。",
        },
    },
    "blood_pressure": {
        "desc": "blood pressure control (person has high blood pressure)",
        "line": {
            "ko": "혈압을 꾸준히 관리하면 눈 속 혈관에 주는 부담을 줄일 수 있습니다.",
            "en": "Keeping your blood pressure under control reduces strain on the blood vessels inside your eyes.",
            "es": "Controlar la presión arterial reduce la carga sobre los vasos sanguíneos del ojo.",
            "fr": "Contrôler votre tension artérielle réduit la charge sur les vaisseaux de l’œil.",
            "ja": "血圧をきちんと管理すると、目の中の血管への負担を減らせます。",
            "zh": "控制好血压可以减轻眼内血管的负担。",
        },
        "why": {
            "ko": "높은 혈압이 오래가면 망막 혈관에도 부담이 가므로, 처방받은 약이 있다면 꾸준히 복용하고 생활 습관으로 혈압을 관리하는 것이 좋습니다.",
            "en": "Long-term high blood pressure also strains the retina's blood vessels, so take any prescribed treatment regularly and manage it with daily habits.",
            "es": "La presión alta mantenida también afecta a los vasos de la retina; si tiene tratamiento, tómelo con regularidad y cuide sus hábitos diarios.",
            "fr": "Une tension élevée sur la durée fatigue aussi les vaisseaux de la rétine : prenez régulièrement un éventuel traitement et adaptez vos habitudes.",
            "ja": "高血圧が続くと網膜の血管にも負担がかかるため、処方薬があればきちんと飲み、生活習慣でも血圧を管理しましょう。",
            "zh": "长期高血压也会加重视网膜血管的负担，如有处方药请按时服用，并通过生活习惯控制血压。",
        },
    },
    "quit_smoking": {
        "desc": "quitting smoking (person currently smokes)",
        "line": {
            "ko": "담배를 끊으면 여러 눈 질환의 위험을 줄이는 데 도움이 됩니다.",
            "en": "Quitting smoking helps lower the risk of several eye diseases.",
            "es": "Dejar de fumar ayuda a reducir el riesgo de varias enfermedades oculares.",
            "fr": "Arrêter de fumer aide à réduire le risque de plusieurs maladies des yeux.",
            "ja": "禁煙すると、いくつかの目の病気のリスクを下げるのに役立ちます。",
            "zh": "戒烟有助于降低多种眼病的风险。",
        },
        "why": {
            "ko": "흡연은 수정체와 망막 모두에 해로운 것으로 알려져 있어, 보건소 금연 클리닉 같은 도움을 받아 보세요.",
            "en": "Smoking is known to harm both the lens and the retina; free quit-smoking services can help.",
            "es": "Fumar perjudica tanto al cristalino como a la retina; los programas para dejar de fumar pueden ayudarle.",
            "fr": "Le tabac nuit au cristallin comme à la rétine ; les services d’aide à l’arrêt du tabac peuvent vous accompagner.",
            "ja": "喫煙は水晶体にも網膜にも悪影響があるとされています。禁煙外来などのサポートを利用しましょう。",
            "zh": "吸烟对晶状体和视网膜都有害，可以借助戒烟门诊等帮助。",
        },
    },
    "night_driving": {
        "desc": "reduce night driving and keep windshield/glasses clean (person reports glare)",
        "line": {
            "ko": "밤에 빛 번짐이 심하면 야간 운전을 줄이고, 운전 전에는 앞유리와 안경을 깨끗이 닦으세요.",
            "en": "If glare is strong at night, drive less after dark and clean your windshield and glasses before driving.",
            "es": "Si el deslumbramiento nocturno es fuerte, conduzca menos de noche y limpie el parabrisas y las gafas antes de conducir.",
            "fr": "Si l’éblouissement est fort la nuit, conduisez moins après la tombée du jour et nettoyez pare-brise et lunettes avant de prendre la route.",
            "ja": "夜の光のにじみが強いときは夜間の運転を減らし、運転前にフロントガラスと眼鏡をきれいにしましょう。",
            "zh": "如果夜间眩光明显，请减少夜间驾驶，开车前擦净挡风玻璃和眼镜。",
        },
        "why": {
            "ko": "빛 번짐은 밤에 맞은편 전조등을 볼 때 특히 심해질 수 있어, 안과에서 원인을 확인하기 전까지는 무리한 야간 운전을 피하는 것이 안전합니다.",
            "en": "Glare can be worst when facing oncoming headlights at night, so avoid unnecessary night driving until an eye doctor has checked the cause.",
            "es": "El deslumbramiento puede empeorar con los faros de frente por la noche; evite conducir de noche si no es necesario hasta que un oftalmólogo revise la causa.",
            "fr": "L’éblouissement peut être pire face aux phares la nuit : évitez la conduite nocturne non indispensable tant qu’un ophtalmologiste n’en a pas vérifié la cause.",
            "ja": "光のにじみは夜の対向車のライトで特に強くなることがあるため、眼科で原因を確認するまでは無理な夜間運転を避けましょう。",
            "zh": "眩光在夜间面对对向车灯时可能最明显，在眼科查明原因之前，请避免不必要的夜间驾驶。",
        },
    },
    "home_amsler": {
        "desc": "check the Amsler grid at home one eye at a time (central vision)",
        "line": {
            "ko": "집에서도 암슬러 격자를 한쪽 눈씩 주기적으로 보고, 선이 새로 휘어 보이면 바로 안과에 가세요.",
            "en": "Check the Amsler grid at home one eye at a time, and see an eye doctor promptly if lines newly look wavy.",
            "es": "Revise la rejilla de Amsler en casa con un ojo cada vez y acuda pronto al oftalmólogo si las líneas empiezan a verse onduladas.",
            "fr": "Regardez la grille d’Amsler chez vous, un œil à la fois, et consultez rapidement si des lignes deviennent ondulées.",
            "ja": "自宅でもアムスラーグリッドを片目ずつ定期的に見て、線が新たにゆがんで見えたらすぐ眼科に行きましょう。",
            "zh": "在家也请每次用一只眼睛定期看阿姆斯勒方格表，如果线条新出现弯曲，请尽快去眼科。",
        },
        "why": {
            "ko": "중심 시야의 변화는 다른 쪽 눈이 가려 주면 알아차리기 어려워서, 한쪽 눈씩 확인하는 습관이 변화를 빨리 발견하는 데 도움이 됩니다.",
            "en": "Changes in central vision are easy to miss when the other eye compensates, so checking one eye at a time helps catch them early.",
            "es": "Los cambios en la visión central pasan desapercibidos cuando el otro ojo compensa; revisar un ojo cada vez ayuda a detectarlos pronto.",
            "fr": "Un changement de la vision centrale passe inaperçu quand l’autre œil compense ; vérifier un œil à la fois aide à le repérer tôt.",
            "ja": "中心の見え方の変化は、もう片方の目が補うと気づきにくいため、片目ずつ確認する習慣が早期発見に役立ちます。",
            "zh": "中心视力的变化在另一只眼睛代偿时不易察觉，每次检查一只眼睛有助于及早发现。",
        },
    },
    "reading_light": {
        "desc": "bright, even reading light (person reports hazy or blurry vision)",
        "line": {
            "ko": "글을 읽을 때는 밝고 고른 조명을 쓰고, 눈부심이 덜한 곳에서 보세요.",
            "en": "Use bright, even lighting when reading, and avoid spots with harsh glare.",
            "es": "Use una luz brillante y uniforme para leer y evite los lugares con reflejos fuertes.",
            "fr": "Lisez avec un éclairage vif et uniforme, à l’écart des reflets gênants.",
            "ja": "文字を読むときは明るく均一な照明を使い、まぶしい場所は避けましょう。",
            "zh": "阅读时请使用明亮、均匀的照明，避开刺眼的地方。",
        },
        "why": {
            "ko": "시야가 뿌옇거나 흐릴 때는 조명이 어두우면 더 불편하게 느껴질 수 있습니다.",
            "en": "When vision feels hazy or blurry, dim light can make it feel worse.",
            "es": "Cuando la vista está nublada o borrosa, la poca luz puede empeorar la sensación.",
            "fr": "Quand la vue est voilée ou floue, une lumière faible peut accentuer la gêne.",
            "ja": "かすみやぼやけがあるときは、暗い照明だとより見えにくく感じることがあります。",
            "zh": "视物模糊或有雾感时，光线太暗会让人感觉更不舒服。",
        },
    },
    "uv": {
        "desc": "daytime UV protection with sunglasses or a hat",
        "line": {
            "ko": "낮에 밖에 나갈 때는 자외선 차단 선글라스나 챙 있는 모자로 눈을 보호하세요.",
            "en": "When you go outside in the daytime, protect your eyes with UV-blocking sunglasses or a wide-brimmed hat.",
            "es": "Cuando salga de día, proteja sus ojos con gafas de sol con filtro UV o una gorra con visera.",
            "fr": "Quand vous sortez en journée, protégez vos yeux avec des lunettes de soleil anti-UV ou un chapeau à larges bords.",
            "ja": "日中に外出するときは、UVカットのサングラスやつばの広い帽子で目を守りましょう。",
            "zh": "白天外出时，请戴防紫外线太阳镜或宽檐帽保护眼睛。",
        },
        "why": {
            "ko": "오랜 자외선 노출은 수정체가 뿌옇게 변하는 원인 중 하나로 알려져 있습니다.",
            "en": "Long-term UV exposure is one of the known causes of the lens becoming cloudy.",
            "es": "La exposición prolongada a la radiación UV es una de las causas conocidas de que el cristalino se vuelva opaco.",
            "fr": "Une exposition prolongée aux UV est l’une des causes connues d’opacification du cristallin.",
            "ja": "長年の紫外線は水晶体が濁る原因の一つとして知られています。",
            "zh": "长期紫外线照射是已知导致晶状体变浑浊的原因之一。",
        },
    },
    "eye_rest": {
        "desc": "screen breaks: look far away for 20 seconds every 20 minutes",
        "line": {
            "ko": "화면을 오래 볼 때는 20분마다 20초쯤 먼 곳을 바라보며 눈을 쉬게 하세요.",
            "en": "When looking at screens for a long time, rest your eyes by looking far away for about 20 seconds every 20 minutes.",
            "es": "Si mira pantallas mucho tiempo, descanse la vista mirando a lo lejos unos 20 segundos cada 20 minutos.",
            "fr": "Devant un écran, reposez vos yeux en regardant au loin environ 20 secondes toutes les 20 minutes.",
            "ja": "画面を長く見るときは、20分ごとに20秒ほど遠くを見て目を休めましょう。",
            "zh": "长时间看屏幕时，每20分钟看远处约20秒，让眼睛休息一下。",
        },
        "why": {
            "ko": "가까운 곳을 오래 보면 눈이 쉽게 피로해지고 건조해지므로, 자주 깜빡이고 쉬는 습관이 도움이 됩니다.",
            "en": "Long periods of close work tire and dry the eyes, so blinking often and taking breaks helps.",
            "es": "Mirar de cerca durante mucho tiempo cansa y reseca los ojos; parpadear a menudo y hacer pausas ayuda.",
            "fr": "Regarder de près longtemps fatigue et assèche les yeux : cligner souvent et faire des pauses aide.",
            "ja": "近くを長時間見ると目が疲れて乾きやすいため、まばたきと休憩の習慣が役立ちます。",
            "zh": "长时间近距离用眼容易让眼睛疲劳、干涩，经常眨眼和休息会有帮助。",
        },
    },
}

# ── 3줄째: 검진 권유 / 마무리 ────────────────────────────────────────────
CLOSING = {
    "visit_soon": {
        "desc": "see an eye doctor soon, as the on-screen recommended action says",
        "line": {
            "ko": "화면의 권장 조치대로 가까운 시일 안에 안과 진료를 받으세요.",
            "en": "Following the recommended action above, see an eye doctor soon.",
            "es": "Siguiendo la acción recomendada, acuda pronto al oftalmólogo.",
            "fr": "Comme recommandé ci-dessus, consultez un ophtalmologiste prochainement.",
            "ja": "上の推奨対応のとおり、近いうちに眼科を受診してください。",
            "zh": "请按照上方的建议措施，尽快到眼科就诊。",
        },
        "why": {
            "ko": "사진이나 자가검사에서 확인이 필요한 신호가 있었기 때문에, 생활 관리보다 진료가 먼저입니다.",
            "en": "A sign that needs checking came up in the photo or self-test, so seeing a doctor comes before lifestyle changes.",
            "es": "La foto o la autoprueba mostró una señal que conviene revisar, así que la consulta va antes que los cambios de hábitos.",
            "fr": "La photo ou l’autotest a montré un signe à vérifier : la consultation passe avant les changements d’habitudes.",
            "ja": "写真や自己チェックで確認が必要なサインがあったため、生活習慣の見直しより受診が先です。",
            "zh": "照片或自测中出现了需要确认的信号，因此就诊比调整生活习惯更优先。",
        },
    },
    "visit_weeks": {
        "desc": "book an eye exam within a few weeks, as the on-screen recommended action says",
        "line": {
            "ko": "화면의 권장 조치대로 몇 주 안에 안과 검진 일정을 잡아 보세요.",
            "en": "Following the recommended action above, book an eye exam within the next few weeks.",
            "es": "Siguiendo la acción recomendada, pida cita de revisión ocular en las próximas semanas.",
            "fr": "Comme recommandé ci-dessus, prenez rendez-vous pour un examen des yeux dans les prochaines semaines.",
            "ja": "上の推奨対応のとおり、数週間以内に眼科検診の予約を入れましょう。",
            "zh": "请按照上方的建议措施，在几周内预约眼科检查。",
        },
        "why": {
            "ko": "지금 서둘러야 하는 신호는 아니지만, 확인이 필요한 항목이 있어 미루지 않는 것이 좋습니다.",
            "en": "It is not an emergency, but some items need checking, so it is better not to put it off.",
            "es": "No es una urgencia, pero hay aspectos que conviene revisar, así que es mejor no aplazarlo.",
            "fr": "Ce n’est pas une urgence, mais certains points méritent d’être vérifiés : mieux vaut ne pas repousser.",
            "ja": "急ぐサインではありませんが、確認が必要な項目があるため先延ばしにしないほうがよいでしょう。",
            "zh": "这不是紧急情况，但有需要确认的项目，最好不要拖延。",
        },
    },
    "exam_overdue": {
        "desc": "get the eye exam that has been put off (no eye exam in the last 2 years)",
        "line": {
            "ko": "최근 2년 동안 안과 검진을 받지 않았다면 이번 기회에 한 번 받아 보세요.",
            "en": "If you have not had an eye exam in the last two years, take this chance to get one.",
            "es": "Si no se ha revisado la vista en los últimos dos años, aproveche para hacerlo ahora.",
            "fr": "Si vous n’avez pas fait d’examen des yeux depuis deux ans, profitez-en pour en faire un.",
            "ja": "ここ2年ほど眼科検診を受けていなければ、この機会に受けてみましょう。",
            "zh": "如果最近两年没有做过眼科检查，不妨借这个机会做一次。",
        },
        "why": {
            "ko": "눈 질환 중에는 초기에 증상이 거의 없는 것이 많아, 불편함이 없어도 확인해 두는 것이 중요합니다.",
            "en": "Many eye diseases cause few symptoms early on, so a check matters even without discomfort.",
            "es": "Muchas enfermedades oculares apenas dan síntomas al principio, por eso conviene revisarse aunque no note molestias.",
            "fr": "Beaucoup de maladies des yeux donnent peu de symptômes au début : un contrôle compte même sans gêne.",
            "ja": "目の病気には初期にほとんど症状がないものも多く、不調がなくても確認しておくことが大切です。",
            "zh": "许多眼病早期几乎没有症状，即使没有不适，检查一下也很重要。",
        },
    },
    "diabetic_yearly": {
        "desc": "yearly dilated retina exam because of diabetes",
        "line": {
            "ko": "당뇨가 있으면 눈에 불편함이 없어도 해마다 안저 검사를 받는 것이 권장됩니다.",
            "en": "With diabetes, a yearly dilated retina exam is recommended even if your eyes feel fine.",
            "es": "Con diabetes se recomienda un fondo de ojo cada año, aunque no note molestias en los ojos.",
            "fr": "En cas de diabète, un fond d’œil chaque année est recommandé, même sans gêne visuelle.",
            "ja": "糖尿病がある場合は、目に不調がなくても毎年眼底検査を受けることがすすめられています。",
            "zh": "有糖尿病的人，即使眼睛没有不适，也建议每年做一次眼底检查。",
        },
        "why": {
            "ko": "당뇨로 인한 망막 변화는 초기에 증상이 없는 경우가 많아, 해마다 안저 검사로 일찍 찾는 것이 중요합니다.",
            "en": "Diabetes-related changes in the retina often cause no symptoms early, so yearly retina checks help find them in time.",
            "es": "Los cambios de la retina por la diabetes suelen no dar síntomas al principio; el fondo de ojo anual ayuda a detectarlos a tiempo.",
            "fr": "Les atteintes de la rétine liées au diabète sont souvent silencieuses au début ; le fond d’œil annuel aide à les repérer à temps.",
            "ja": "糖尿病による網膜の変化は初期に症状がないことが多いため、毎年の眼底検査で早めに見つけることが大切です。",
            "zh": "糖尿病引起的视网膜变化早期常常没有症状，每年做眼底检查有助于及时发现。",
        },
    },
    "glaucoma_followup": {
        "desc": "keep having eye pressure and optic nerve checks (told eye pressure is high)",
        "line": {
            "ko": "안압이 높다는 말을 들었다면 안압과 시신경 검사를 꾸준히 받아 보세요.",
            "en": "If you have been told your eye pressure is high, have your eye pressure and optic nerve checked at regular intervals.",
            "es": "Si le han dicho que tiene la presión ocular alta, hágase controles de la presión y del nervio óptico a intervalos regulares.",
            "fr": "Si l’on vous a dit que votre pression oculaire est élevée, faites contrôler la pression et le nerf optique à intervalles réguliers.",
            "ja": "眼圧が高いと言われたことがあるなら、眼圧と視神経の検査を定期的に受けましょう。",
            "zh": "如果曾被告知眼压偏高，请定期检查眼压和视神经。",
        },
        "why": {
            "ko": "시신경 변화는 서서히 진행되고 초기에 알아차리기 어려워, 정해진 간격으로 확인하는 것이 중요합니다.",
            "en": "Optic nerve changes develop slowly and are hard to notice early, so checks at set intervals matter.",
            "es": "Los cambios del nervio óptico avanzan despacio y cuesta notarlos al principio; por eso importan los controles a intervalos fijos.",
            "fr": "Les atteintes du nerf optique progressent lentement et passent inaperçues au début : des contrôles réguliers sont importants.",
            "ja": "視神経の変化はゆっくり進み初期には気づきにくいため、決まった間隔で確認することが大切です。",
            "zh": "视神经的变化进展缓慢、早期不易察觉，按规定间隔检查很重要。",
        },
    },
    "regular_40": {
        "desc": "eye exam every 1-2 years after age 40 even without symptoms",
        "line": {
            "ko": "40세가 넘으면 증상이 없어도 1~2년마다 안과 검진을 받는 것이 좋습니다.",
            "en": "After 40, an eye exam every 1–2 years is a good idea even without symptoms.",
            "es": "A partir de los 40, conviene una revisión ocular cada 1–2 años aunque no haya síntomas.",
            "fr": "Après 40 ans, un examen des yeux tous les 1 à 2 ans est conseillé, même sans symptôme.",
            "ja": "40歳を過ぎたら、症状がなくても1〜2年ごとに眼科検診を受けるのがおすすめです。",
            "zh": "40岁以后，即使没有症状，也建议每1～2年做一次眼科检查。",
        },
        "why": {
            "ko": "나이가 들수록 눈 질환이 늘어나므로, 검진으로 변화를 일찍 확인할 수 있습니다.",
            "en": "Eye diseases become more common with age, so exams help spot changes early.",
            "es": "Las enfermedades oculares aumentan con la edad; las revisiones ayudan a detectar cambios pronto.",
            "fr": "Les maladies des yeux deviennent plus fréquentes avec l’âge : les examens aident à repérer tôt les changements.",
            "ja": "年齢とともに目の病気は増えるため、検診で変化を早く見つけられます。",
            "zh": "随着年龄增长眼病会增多，检查有助于及早发现变化。",
        },
    },
    "regular_young": {
        "desc": "get an eye exam without delay if eyes feel uncomfortable or vision changes (under 40)",
        "line": {
            "ko": "눈이 불편하거나 보이는 것이 달라지면 미루지 말고 안과 검진을 받으세요.",
            "en": "If your eyes feel uncomfortable or your vision changes, get an eye exam without delay.",
            "es": "Si nota molestias o cambios en la visión, hágase una revisión sin demora.",
            "fr": "En cas de gêne ou de changement de la vue, faites un examen sans tarder.",
            "ja": "目の不調や見え方の変化があれば、先延ばしにせず眼科検診を受けましょう。",
            "zh": "如果眼睛不适或视力有变化，请及时做眼科检查。",
        },
        "why": {
            "ko": "젊더라도 시력 변화나 눈의 불편함은 원인을 확인해 두는 것이 좋습니다.",
            "en": "Even at a younger age, vision changes or eye discomfort are worth having checked.",
            "es": "Aunque sea joven, conviene revisar los cambios de visión o las molestias oculares.",
            "fr": "Même jeune, un changement de vision ou une gêne oculaire mérite d’être vérifié.",
            "ja": "若くても、見え方の変化や目の不調は原因を確認しておくとよいでしょう。",
            "zh": "即使年轻，视力变化或眼部不适也值得检查原因。",
        },
    },
    "warning_signs": {
        "desc": "go right away for sudden vision loss, new flashes or a curtain-like shadow",
        "line": {
            "ko": "갑자기 시력이 떨어지거나 번쩍임, 커튼 같은 가림이 생기면 바로 안과에 가세요.",
            "en": "If your vision drops suddenly, or you see new flashes or a curtain-like shadow, go to an eye doctor right away.",
            "es": "Si pierde visión de repente o ve destellos nuevos o una sombra como una cortina, acuda de inmediato al oftalmólogo.",
            "fr": "En cas de baisse brutale de la vue, de nouveaux éclairs ou d’une ombre en forme de rideau, consultez immédiatement.",
            "ja": "急に視力が落ちたり、光が走る・カーテンのような影が見えたりしたら、すぐに眼科へ行きましょう。",
            "zh": "如果视力突然下降，或出现新的闪光、帘子般的遮挡，请立即去眼科。",
        },
        "why": {
            "ko": "이런 증상은 몇 시간 차이로 결과가 달라질 수 있는 응급 신호일 수 있습니다.",
            "en": "These can be emergency signs where a few hours can make a difference.",
            "es": "Pueden ser señales de urgencia en las que unas horas marcan la diferencia.",
            "fr": "Ce peuvent être des signes d’urgence où quelques heures comptent.",
            "ja": "こうした症状は、数時間の差で結果が変わりうる緊急のサインのことがあります。",
            "zh": "这些可能是紧急信号，几个小时的差别就可能影响结果。",
        },
    },
}


# 맞춤 질문에 "예"라고 답한 주제(ans_*)에서 열리는 마무리 조언(2026-09-28).
# 예전에는 맞춤 질문의 답이 아무 데도 쓰이지 않았다 — 이제 답에 따라 AI가 고를 수 있는 조언이 달라진다.
CLOSING.update({
    "mention_injury": {
        "desc": "tell the doctor about a past eye injury (answered Yes to eye injury)",
        "line": {
            "ko": "예전에 눈을 다친 적이 있다면 진료 때 꼭 알려 주세요.",
            "en": "If you have injured an eye before, be sure to mention it at your visit.",
            "es": "Si alguna vez se lesionó un ojo, menciónelo en la consulta.",
            "fr": "Si vous vous êtes déjà blessé un œil, signalez-le lors de la consultation.",
            "ja": "以前に目をけがしたことがあれば、受診時に必ず伝えてください。",
            "zh": "如果以前眼睛受过伤，请在就诊时一定告诉医生。",
        },
        "why": {
            "ko": "오래전 눈 외상도 수정체나 안압에 영향을 줄 수 있어 의사가 진료할 때 참고합니다.",
            "en": "Even an old eye injury can affect the lens or eye pressure, so doctors take it into account.",
            "es": "Incluso una lesión antigua puede afectar al cristalino o a la presión ocular, y el médico lo tiene en cuenta.",
            "fr": "Même une ancienne blessure peut affecter le cristallin ou la pression de l’œil ; le médecin en tient compte.",
            "ja": "昔の目のけがでも水晶体や眼圧に影響することがあり、医師が診察の参考にします。",
            "zh": "即使是很久以前的眼外伤，也可能影响晶状体或眼压，医生会作为参考。",
        },
    },
    "bring_drops": {
        "desc": "bring current eye drops or their names to the visit (answered Yes to recent eye drop use)",
        "line": {
            "ko": "지금 쓰고 있는 안약이 있다면 진료 때 가져가거나 이름을 알려 주세요.",
            "en": "If you use eye drops, bring them or tell the doctor their names at your visit.",
            "es": "Si usa gotas para los ojos, llévelas a la consulta o indique su nombre.",
            "fr": "Si vous utilisez des gouttes, apportez-les ou donnez leur nom lors de la consultation.",
            "ja": "使っている目薬があれば、受診時に持参するか名前を伝えてください。",
            "zh": "如果正在使用眼药水，请就诊时带上或告诉医生药名。",
        },
        "why": {
            "ko": "일부 안약(예: 스테로이드 안약)은 오래 쓰면 눈에 영향을 줄 수 있어 의사가 확인합니다.",
            "en": "Some drops, such as steroid drops, can affect the eye with long-term use, so the doctor will want to check.",
            "es": "Algunas gotas, como las de corticoides, pueden afectar al ojo con el uso prolongado; el médico querrá revisarlas.",
            "fr": "Certaines gouttes, comme les corticoïdes, peuvent agir sur l’œil à long terme ; le médecin voudra les vérifier.",
            "ja": "ステロイド点眼薬など一部の目薬は長く使うと目に影響することがあり、医師が確認します。",
            "zh": "部分眼药水（如激素类眼药水）长期使用可能影响眼睛，医生需要确认。",
        },
    },
    "mention_impact": {
        "desc": "describe everyday activities made harder at the visit (answered Yes to daily impact)",
        "line": {
            "ko": "눈 때문에 불편해진 일상 활동이 있다면 진료 때 구체적으로 말씀하세요.",
            "en": "If your eyes make everyday activities harder, describe them at your visit.",
            "es": "Si sus ojos le dificultan actividades diarias, descríbalas en la consulta.",
            "fr": "Si vos yeux gênent vos activités quotidiennes, décrivez-les lors de la consultation.",
            "ja": "目のせいで不便になった日常の活動があれば、受診時に具体的に伝えましょう。",
            "zh": "如果眼睛问题让日常活动变得困难，请在就诊时具体说明。",
        },
        "why": {
            "ko": "일상생활에 얼마나 불편한지는 치료 시기를 정할 때 의사가 중요하게 보는 정보입니다.",
            "en": "How much your daily life is affected is important information when the doctor decides on the timing of treatment.",
            "es": "Cuánto afecta a su vida diaria es un dato importante cuando el médico decide el momento del tratamiento.",
            "fr": "L’impact sur la vie quotidienne est une information importante pour décider du moment d’un traitement.",
            "ja": "日常生活への影響の大きさは、医師が治療の時期を決めるときに重視する情報です。",
            "zh": "日常生活受影响的程度，是医生决定治疗时机的重要信息。",
        },
    },
    "sugar_consult": {
        "desc": "plan eye checks with the diabetes doctor (answered Yes to blood sugar often above target)",
        "line": {
            "ko": "혈당이 목표보다 자주 높다면 당뇨 진료 때 눈 검사 계획도 함께 상의해 보세요.",
            "en": "If your blood sugar is often above target, discuss an eye check plan at your diabetes visits too.",
            "es": "Si su glucosa suele estar por encima del objetivo, hable también de un plan de revisión ocular en sus consultas de diabetes.",
            "fr": "Si votre glycémie dépasse souvent l’objectif, parlez aussi d’un suivi des yeux lors de vos consultations pour le diabète.",
            "ja": "血糖が目標より高いことが多いなら、糖尿病の受診時に目の検査の予定も相談しましょう。",
            "zh": "如果血糖经常高于目标，看糖尿病门诊时也请一起商量眼部检查计划。",
        },
        "why": {
            "ko": "혈당 조절이 어려울수록 망막 변화가 생기기 쉬워 안저 검사를 더 챙기는 것이 좋습니다.",
            "en": "Retina changes become more common when blood sugar is hard to control, so retina checks matter more.",
            "es": "Los cambios en la retina son más frecuentes cuando cuesta controlar la glucosa, por eso importa más revisarla.",
            "fr": "Les atteintes de la rétine sont plus fréquentes quand la glycémie est difficile à équilibrer : le contrôle de la rétine compte davantage.",
            "ja": "血糖のコントロールが難しいほど網膜の変化が起こりやすいため、眼底検査がより大切です。",
            "zh": "血糖越难控制，视网膜越容易出现变化，因此眼底检查更为重要。",
        },
    },
    "quit_help": {
        "desc": "free quit-smoking support (answered Yes to wanting help to quit smoking)",
        "line": {
            "ko": "담배를 끊고 싶다면 보건소 금연클리닉에서 무료로 도움을 받을 수 있어요.",
            "en": "If you want to quit smoking, free quit-smoking services can help.",
            "es": "Si quiere dejar de fumar, los servicios gratuitos para dejar de fumar pueden ayudarle.",
            "fr": "Si vous voulez arrêter de fumer, des services gratuits d’aide à l’arrêt peuvent vous accompagner.",
            "ja": "禁煙したいなら、禁煙外来や無料の相談窓口のサポートを受けられます。",
            "zh": "如果想戒烟，可以借助免费的戒烟服务。",
        },
        "why": {
            "ko": "금연 상담과 약물 지원을 함께 받으면 혼자 할 때보다 성공하기 쉽습니다.",
            "en": "Counselling together with medication support makes quitting easier than trying alone.",
            "es": "El asesoramiento junto con apoyo farmacológico facilita dejarlo más que intentarlo solo.",
            "fr": "Un accompagnement associé à une aide médicamenteuse facilite l’arrêt par rapport à un essai seul.",
            "ja": "カウンセリングと薬のサポートを組み合わせると、一人で挑戦するより成功しやすくなります。",
            "zh": "咨询加药物辅助，比独自尝试更容易成功。",
        },
    },
})

# ── 수술 4주 이내(술후 문진) ────────────────────────────────────────────
# 1줄째는 앱이 이미 정한 권장 조치(computeTriage → postoperativeTriage)를 그대로 옮긴다. AI가 고르지 않는다.
POST_ACTION = {
    "now": {
        "line": {
            "ko": "새로 생긴 증상을 수술한 병원에 알리고, 예정된 진료까지 기다려도 되는지 확인하세요.",
            "en": "Tell the hospital that performed your surgery about the new symptoms and ask whether it is safe to wait until your scheduled review.",
            "es": "Comunique los síntomas nuevos al hospital que le operó y pregunte si puede esperar hasta la revisión programada.",
            "fr": "Signalez les nouveaux symptômes à l’hôpital qui vous a opéré et demandez si vous pouvez attendre le contrôle prévu.",
            "ja": "新しく出た症状を手術を受けた病院に伝え、予定の受診まで待ってよいか確認しましょう。",
            "zh": "请把新出现的症状告诉为您手术的医院，并确认能否等到预约的复诊。",
        },
        "why": {
            "ko": "수술 후 증상의 원인은 수술한 병원이 가장 정확하게 판단할 수 있습니다.",
            "en": "The hospital that performed your surgery is best placed to judge the cause of postoperative symptoms.",
            "es": "El hospital que le operó es quien mejor puede valorar la causa de los síntomas tras la cirugía.",
            "fr": "L’hôpital qui vous a opéré est le mieux placé pour juger la cause des symptômes après l’opération.",
            "ja": "術後の症状の原因は、手術を受けた病院がいちばん正確に判断できます。",
            "zh": "术后症状的原因，由为您手术的医院判断最准确。",
        },
    },
    "confirm": {
        "line": {
            "ko": "수술한 병원에 연락해 눈 관리 방법과 다음 진료 일정을 다시 확인하세요.",
            "en": "Contact the hospital that performed your surgery to re-confirm how to care for your eye and when your next review is.",
            "es": "Contacte al hospital que le operó para confirmar de nuevo los cuidados del ojo y la fecha de la próxima revisión.",
            "fr": "Contactez l’hôpital qui vous a opéré pour reconfirmer les soins de l’œil et la date du prochain contrôle.",
            "ja": "手術を受けた病院に連絡し、目のケア方法と次回の受診日をもう一度確認しましょう。",
            "zh": "请联系为您手术的医院，再次确认眼睛的护理方法和下次复诊时间。",
        },
        "why": {
            "ko": "경고 증상은 없었지만, 관리 방법을 정확히 알아야 회복 중에 생길 수 있는 문제를 줄일 수 있습니다.",
            "en": "You reported no warning signs, but knowing your aftercare clearly helps avoid problems during recovery.",
            "es": "No indicó signos de alarma, pero conocer bien los cuidados ayuda a evitar problemas durante la recuperación.",
            "fr": "Vous n’avez signalé aucun signe d’alerte, mais bien connaître les soins aide à éviter des problèmes pendant la récupération.",
            "ja": "警告症状はありませんでしたが、ケア方法をきちんと知っておくと回復中のトラブルを減らせます。",
            "zh": "您没有报告警示症状，但清楚了解护理方法有助于减少恢复期的问题。",
        },
    },
    "follow": {
        "line": {
            "ko": "퇴원 안내와 예정된 진료 일정을 그대로 따르고, 증상이 새로 생기거나 나빠지면 수술한 병원에 연락하세요.",
            "en": "Keep following your discharge instructions and scheduled review, and contact the hospital that performed your surgery if symptoms appear or get worse.",
            "es": "Siga las indicaciones del alta y la revisión programada, y contacte al hospital que le operó si aparecen o empeoran los síntomas.",
            "fr": "Suivez les consignes de sortie et le contrôle prévu, et contactez l’hôpital qui vous a opéré si des symptômes apparaissent ou s’aggravent.",
            "ja": "退院時の説明と予定の受診を守り、症状が出たり悪化したりしたら手術を受けた病院に連絡しましょう。",
            "zh": "请遵循出院指导和预约的复诊，如出现新症状或症状加重，请联系为您手术的医院。",
        },
        "why": {
            "ko": "이번 문진에서는 경고 증상이 보고되지 않았지만, 이 문진만으로 회복 상태를 판단할 수는 없습니다.",
            "en": "No warning signs were reported in this questionnaire, but it cannot judge how you are healing.",
            "es": "En este cuestionario no se indicaron signos de alarma, pero no permite valorar la recuperación.",
            "fr": "Aucun signe d’alerte n’a été signalé, mais ce questionnaire ne permet pas de juger la guérison.",
            "ja": "今回の問診では警告症状はありませんでしたが、この問診だけで回復の状態は判断できません。",
            "zh": "本次问诊未报告警示症状，但仅凭问诊无法判断恢复情况。",
        },
    },
}

POST_CARE = {
    "tell_changes": {
        "desc": "at the visit, tell the hospital exactly what feels wrong and since when (symptoms were reported)",
        "line": {
            "ko": "진료 때는 불편한 점과 언제부터 그랬는지를 수술한 병원에 구체적으로 말씀하세요.",
            "en": "At your visit, tell the hospital exactly what feels wrong and since when.",
            "es": "En la consulta, explique con detalle qué molestias tiene y desde cuándo.",
            "fr": "Lors de la consultation, décrivez précisément la gêne et depuis quand elle dure.",
            "ja": "受診時には、気になる症状といつからかを具体的に伝えましょう。",
            "zh": "复诊时，请具体说明哪里不舒服以及从什么时候开始。",
        },
        "why": {
            "ko": "증상이 생긴 시점과 변화를 알려 주면 의료진이 상태를 판단하는 데 도움이 됩니다.",
            "en": "Telling them when symptoms started and how they changed helps the doctors judge your condition.",
            "es": "Indicar cuándo empezaron los síntomas y cómo cambiaron ayuda al médico a valorar su estado.",
            "fr": "Préciser quand les symptômes ont commencé et comment ils ont évolué aide les médecins à juger votre état.",
            "ja": "症状が始まった時期や変化を伝えると、医師が状態を判断しやすくなります。",
            "zh": "说明症状开始的时间和变化，有助于医生判断您的情况。",
        },
    },
    "prepare_questions": {
        "desc": "write down questions about drops, washing and exercise for the next visit",
        "line": {
            "ko": "다음 진료 때 물어볼 것(안약 쓰는 법, 세수·운동을 다시 시작해도 되는 때 등)을 미리 적어 가세요.",
            "en": "Write down questions for your next visit, such as how to use your drops and when you can wash your face or exercise again.",
            "es": "Anote preguntas para la próxima consulta, como el uso de las gotas y cuándo puede volver a lavarse la cara o hacer ejercicio.",
            "fr": "Notez vos questions pour le prochain rendez-vous, par exemple l’usage des gouttes ou quand reprendre la toilette du visage et le sport.",
            "ja": "次の受診で聞きたいこと（目薬の使い方、洗顔や運動を再開してよい時期など）をメモしておきましょう。",
            "zh": "把下次复诊想问的问题（如眼药水的用法、何时可以洗脸或运动）提前写下来。",
        },
        "why": {
            "ko": "궁금한 점을 적어 가면 짧은 진료 시간에도 관리 방법을 빠짐없이 확인할 수 있습니다.",
            "en": "A written list helps you cover everything about aftercare even in a short visit.",
            "es": "Llevar las preguntas por escrito ayuda a aclarar todos los cuidados aunque la consulta sea breve.",
            "fr": "Une liste écrite aide à tout vérifier sur les soins, même lors d’une consultation courte.",
            "ja": "質問をメモしておくと、短い診察でもケア方法を漏れなく確認できます。",
            "zh": "提前写好问题，即使复诊时间短，也能把护理方法问清楚。",
        },
    },
    "protect_eye": {
        "desc": "use drops and eye shield as instructed, do not rub or press the eye",
        "line": {
            "ko": "수술한 병원이 알려준 대로 안약과 보호대를 사용하고, 눈을 비비거나 누르지 마세요.",
            "en": "Use your eye drops and eye shield as the hospital told you, and do not rub or press on the eye.",
            "es": "Use las gotas y el protector como le indicó el hospital, y no se frote ni presione el ojo.",
            "fr": "Utilisez les gouttes et la coque comme l’hôpital vous l’a indiqué, et ne frottez ni n’appuyez sur l’œil.",
            "ja": "病院の指示どおりに目薬と保護具を使い、目をこすったり押したりしないでください。",
            "zh": "请按医院的指示使用眼药水和护眼罩，不要揉眼或按压眼睛。",
        },
        "why": {
            "ko": "수술한 눈은 회복하는 동안 작은 자극에도 영향을 받을 수 있습니다.",
            "en": "The operated eye can be affected by small knocks or pressure while it heals.",
            "es": "El ojo operado puede verse afectado por pequeños golpes o presión mientras se recupera.",
            "fr": "L’œil opéré peut être sensible au moindre choc ou à la pression pendant la guérison.",
            "ja": "手術した目は回復中、小さな刺激や圧力の影響を受けることがあります。",
            "zh": "手术眼在恢复期间，轻微的碰撞或压力也可能造成影响。",
        },
    },
}

POST_CLOSING = {
    "post_warning": {
        "desc": "contact the surgical hospital or emergency eye service right away if pain worsens or vision drops",
        "line": {
            "ko": "통증이 심해지거나 시력이 갑자기 떨어지면 바로 수술한 병원이나 응급 안과에 연락하세요.",
            "en": "If pain gets worse or your vision suddenly drops, contact the hospital that performed your surgery or an emergency eye service right away.",
            "es": "Si el dolor empeora o la visión baja de repente, contacte de inmediato al hospital que le operó o a urgencias oftalmológicas.",
            "fr": "Si la douleur augmente ou si la vue baisse brutalement, contactez immédiatement l’hôpital qui vous a opéré ou les urgences ophtalmologiques.",
            "ja": "痛みが強くなったり急に視力が落ちたりしたら、すぐに手術を受けた病院か救急の眼科に連絡しましょう。",
            "zh": "如果疼痛加重或视力突然下降，请立即联系为您手术的医院或眼科急诊。",
        },
        "why": {
            "ko": "이런 변화는 가능한 한 빨리 진료를 받아야 하는 신호일 수 있습니다.",
            "en": "Changes like these may need to be seen as soon as possible.",
            "es": "Estos cambios pueden requerir atención lo antes posible.",
            "fr": "Ces changements peuvent nécessiter une consultation au plus vite.",
            "ja": "こうした変化は、できるだけ早く診てもらう必要があるサインのことがあります。",
            "zh": "这类变化可能需要尽快就诊。",
        },
    },
    "post_limit": {
        "desc": "this questionnaire cannot judge recovery; the surgical hospital's review is the reliable guide",
        "line": {
            "ko": "이 문진만으로는 회복 상태를 판단할 수 없으니, 수술한 병원의 진료를 가장 정확한 기준으로 삼으세요.",
            "en": "This questionnaire cannot judge your recovery, so treat the review at your surgical hospital as the reliable guide.",
            "es": "Este cuestionario no puede valorar su recuperación; la revisión en el hospital que le operó es la referencia fiable.",
            "fr": "Ce questionnaire ne peut pas juger votre récupération : fiez-vous au contrôle de l’hôpital qui vous a opéré.",
            "ja": "この問診だけでは回復の状態は判断できないため、手術を受けた病院の診察をいちばん確かな目安にしましょう。",
            "zh": "仅凭本问诊无法判断恢复情况，请以为您手术的医院的复诊为准。",
        },
        "why": {
            "ko": "앱은 알려 주신 내용을 정리할 뿐, 수술한 눈을 직접 보고 판단하지는 못합니다.",
            "en": "The app only organizes what you report; it cannot examine the operated eye.",
            "es": "La aplicación solo ordena lo que usted indica; no puede examinar el ojo operado.",
            "fr": "L’application ne fait que résumer vos réponses ; elle ne peut pas examiner l’œil opéré.",
            "ja": "アプリは申告内容を整理するだけで、手術した目を直接診ることはできません。",
            "zh": "本应用只能整理您报告的内容，无法直接检查手术眼。",
        },
    },
}

_AGE_40_PLUS = {"40s", "50s", "60s", "70s", "80plus"}
_AGE_50_PLUS = {"50s", "60s", "70s", "80plus"}
_GENERIC_CARE = ("uv", "eye_rest")


@dataclass
class Facts:
    flags: set = field(default_factory=set)        # sym_* / risk_* 코드 (언어 중립)
    codes: set = field(default_factory=set)        # 질환 코드 (symptom_codes)
    age: str = ""                                  # 'under10' … '80plus', 모르면 ''
    cataract_code: str = ""
    amsler_abnormal: bool = False
    triage: str = ""                               # now / weeks / monitor / confirm …
    postop: bool = False


def facts_from(symptoms: list[str], flag_codes: list[str] | None, symptom_codes: list[str] | None,
               cataract_code: str, amsler_abnormal: bool, triage_level: str) -> Facts:
    flags = {f for f in (flag_codes or []) if f.startswith(("sym_", "risk_", "ans_"))}
    age = next((f[4:] for f in (flag_codes or []) if f.startswith("age_")), "")
    # 예전 프론트(flag_codes 없음)도 위험요인 '예/아니오'는 언어 중립 문자열로 보낸다.
    for item in symptoms or []:
        low = (item or "").strip().lower()
        if low == "diabetes: yes": flags.add("risk_diabetes")
        if low == "hypertension: yes": flags.add("risk_hypertension")
        if low == "smoking: yes": flags.add("risk_smoking")
    # 반대로 '아니오'라고 명시된 위험요인은 flag_codes에 있어도 믿지 않는다(모순 입력 방어).
    for item in symptoms or []:
        low = (item or "").strip().lower()
        if low == "diabetes: no": flags.discard("risk_diabetes")
        if low == "hypertension: no": flags.discard("risk_hypertension")
    postop = cataract_code == "postop" or any("Eye surgery:" in (s or "") for s in symptoms or [])
    return Facts(flags=flags, codes=set(symptom_codes or []), age=age, cataract_code=cataract_code or "",
                 amsler_abnormal=bool(amsler_abnormal), triage=triage_level or "", postop=postop)


def _post_kind(f: Facts) -> str:
    return {"now": "now", "confirm": "confirm"}.get(f.triage, "follow")


def options_for(f: Facts) -> dict:
    """이 사람에게 해당하는 선택지만 추린다. AI는 여기서만 고를 수 있다."""
    if f.postop:
        kind = _post_kind(f)
        care = ["tell_changes", "protect_eye"] if kind == "now" else ["prepare_questions", "protect_eye"]
        return {"care": care, "closing": ["post_warning", "post_limit"]}

    fl, codes = f.flags, f.codes
    macular = "macular" in codes or f.amsler_abnormal or "sym_amd_center" in fl
    retina = "retinopathy" in codes or "risk_diabetes" in fl
    glaucoma = "glaucoma" in codes or any(x.startswith("sym_gla_") for x in fl)
    cataract_signs = (f.cataract_code in ("risk", "borderline") or "cataract" in codes
                      or any(x.startswith("sym_cat_") for x in fl))

    exams = ["slit_lamp", "dilated_fundus", "iop"]
    if macular or retina: exams.append("oct")
    if glaucoma or "risk_family" in fl: exams.append("visual_field")

    care = []
    if "risk_diabetes" in fl: care.append("glucose")
    if "risk_hypertension" in fl: care.append("blood_pressure")
    if "risk_smoking" in fl: care.append("quit_smoking")
    if "sym_cat_glare" in fl: care.append("night_driving")
    if macular or f.age in _AGE_50_PLUS: care.append("home_amsler")
    if fl & {"sym_cat_foggy", "sym_amd_center", "sym_cat_glasses"}: care.append("reading_light")
    if cataract_signs or "ans_outdoor_time" in fl: care.append("uv")
    if "ans_screen_fatigue" in fl: care.append("eye_rest")
    # 이 사람에게 딱 맞는 조언이 있으면 누구에게나 할 수 있는 일반론(자외선·눈 휴식)은 빼 둔다.
    # 선택지에 남겨 두면 당뇨 환자에게도 '눈 휴식'을 고르는 일이 생긴다.
    if not care:
        care = list(_GENERIC_CARE)

    # 맞춤 질문 답에서 열리는 조언. '진료 때 알릴 것'은 빨리 진료를 받아야 하는 경우에도 쓸모가 있다.
    answered = [advice_id for code, advice_id in (
        ("ans_eye_injury", "mention_injury"), ("ans_eye_drops", "bring_drops"),
        ("ans_daily_impact", "mention_impact"),
        ("ans_sugar_off_target", "sugar_consult"), ("ans_quit_interest", "quit_help")) if code in fl]
    tell = [a for a in answered if a in ("mention_injury", "bring_drops", "mention_impact")]
    if f.triage == "now":
        closing = ["visit_soon", "warning_signs"] + tell
    else:
        specific = []
        if "risk_diabetes" in fl: specific.append("diabetic_yearly")
        if "sym_chk_recent" in fl: specific.append("exam_overdue")
        if "sym_gla_iop" in fl: specific.append("glaucoma_followup")
        specific += answered
        if f.triage == "weeks":
            closing = ["visit_weeks"] + specific
        else:
            regular = "regular_young" if f.age and f.age not in _AGE_40_PLUS else "regular_40"
            closing = specific + [regular, "warning_signs"]
    return {"exams": exams, "care": care, "closing": closing}


def fallback_choice(f: Facts, opts: dict) -> dict:
    """AI가 제대로 고르지 못했을 때의 규칙 기반 선택 — 선택지 목록의 우선순위 그대로."""
    if f.postop:
        return {"care": opts["care"][0], "closing": opts["closing"][0]}
    fl, codes = f.flags, f.codes
    if "retinopathy" in codes or "risk_diabetes" in fl: pair = ["dilated_fundus", "oct"]
    elif "macular" in codes or f.amsler_abnormal: pair = ["oct", "dilated_fundus"]
    elif "glaucoma" in codes and "visual_field" in opts["exams"]: pair = ["iop", "visual_field"]
    else: pair = ["slit_lamp", "dilated_fundus"]
    pair = [e for e in pair if e in opts["exams"]] or opts["exams"][:2]
    if len(pair) < 2:
        pair.append(next(e for e in opts["exams"] if e not in pair))
    return {"exams": pair[:2], "care": opts["care"][0], "closing": opts["closing"][0]}


def apply_choice_priorities(choice: dict, f: Facts, opts: dict) -> dict:
    """Keep valid model picks, but apply high-value priorities already encoded by the facts.

    A schema-valid choice can still ignore a confirmed glaucoma finding or choose a
    generic weeks-to-visit line over an available personalized closing. These rules
    only select from the reviewed options for this person.
    """
    if f.postop:
        return choice

    result = {**choice}
    flags, codes = f.flags, f.codes
    glaucoma = "glaucoma" in codes or any(x.startswith("sym_gla_") for x in flags)
    retina = "retinopathy" in codes or "risk_diabetes" in flags
    macular = "macular" in codes or f.amsler_abnormal or "sym_amd_center" in flags

    # The glaucoma pathway needs both pressure and side-vision checks. Preserve the
    # existing retina/macula priority when several pathways compete for two exam slots.
    if glaucoma and not retina and not macular and "visual_field" in opts["exams"]:
        result["exams"] = ["iop", "visual_field"]

    # The on-screen triage card already carries the weeks timeline; use the closing
    # line for a person's specific risk/history when one is available.
    if result.get("closing") == "visit_weeks":
        specific_closings = [item for item in opts["closing"] if item != "visit_weeks"]
        if specific_closings:
            result["closing"] = specific_closings[0]
    return result


def _catalog(f: Facts):
    return (POST_CARE, POST_CLOSING) if f.postop else (CARE, CLOSING)


def schema_for(f: Facts, opts: dict) -> dict:
    """Ollama format(JSON 스키마). enum 밖의 값은 모델이 아예 생성할 수 없다."""
    props = {"care": {"type": "string", "enum": opts["care"]},
             "closing": {"type": "string", "enum": opts["closing"]}}
    required = ["care", "closing"]
    if not f.postop:
        props["exams"] = {"type": "array", "items": {"type": "string", "enum": opts["exams"]},
                          "minItems": 2, "maxItems": 2}
        required.insert(0, "exams")
    return {"type": "object", "properties": props, "required": required}


def selection_prompt(f: Facts, opts: dict) -> str:
    care_cat, closing_cat = _catalog(f)
    def listing(ids, cat): return "\n".join(f"- {i}: {cat[i]['desc']}" for i in ids)
    facts = sorted(f.flags) + ([f"age_{f.age}"] if f.age else []) + sorted(f"disease_code:{c}" for c in f.codes)
    if f.amsler_abnormal: facts.append("amsler_grid_abnormal")
    if f.cataract_code: facts.append(f"photo_result:{f.cataract_code}")
    if f.triage: facts.append(f"recommended_action:{f.triage}")
    exam_part = ("" if f.postop else
                 "exams: pick the TWO tests this person will most likely have at the eye clinic.\n"
                 f"{listing(opts['exams'], EXAMS)}\n\n")
    return (
        "You help choose eye-care advice for a person who just finished an eye screening app.\n"
        "The app writes the sentences itself. You only CHOOSE option ids.\n"
        f"Person's screening facts (codes): {', '.join(facts) or 'none'}\n"
        "Code meanings: sym_* = a questionnaire item this person flagged, risk_* = a risk factor they have, "
        "sym_chk_recent = no eye exam in 2 years, sym_dr_fundus = no retina exam in the last year, "
        "ans_* = the person answered Yes to a personalized follow-up question on that topic "
        "(an option built for their own answer usually fits best).\n\n"
        f"{exam_part}"
        "care: pick the ONE tip that fits this person's flagged items best "
        "(a tip about their own risk factor or symptom beats a general tip).\n"
        f"{listing(opts['care'], care_cat)}\n\n"
        "closing: pick the ONE closing line that fits best.\n"
        f"{listing(opts['closing'], closing_cat)}\n\n"
        "Answer with JSON only."
    )


def validate_choice(raw, f: Facts, opts: dict) -> dict | None:
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError): return None
    if not isinstance(raw, dict): return None
    care, closing = raw.get("care"), raw.get("closing")
    if care not in opts["care"] or closing not in opts["closing"]: return None
    if f.postop:
        return {"care": care, "closing": closing}
    exams = raw.get("exams")
    if not isinstance(exams, list): return None
    exams = list(dict.fromkeys(e for e in exams if e in opts["exams"]))   # 중복·목록 밖 제거
    if len(exams) < 2: return None
    return {"exams": exams[:2], "care": care, "closing": closing}


# '수 주 내' 단계인데 마무리 문장이 맞춤 문장(당뇨 연 1회 검사 등)이면 그 앞에 붙인다.
# apply_choice_priorities가 visit_weeks를 맞춤 문장으로 바꾸면 요약 3줄에서 '몇 주 안에'가 사라지고
# "해마다 안저 검사"만 남아 1년 뒤에 가도 되는 것처럼 읽힐 수 있었다(2026-09-29 실측 4/4).
WEEKS_LEAD = {
    "ko": "화면의 권장 조치대로 몇 주 안에 안과 검진을 받으세요.",
    "en": "As recommended above, have an eye exam within the next few weeks.",
    "es": "Como indica la acción recomendada, hágase una revisión ocular en las próximas semanas.",
    "fr": "Comme recommandé ci-dessus, faites un examen des yeux dans les prochaines semaines.",
    "ja": "上の推奨対応のとおり、数週間以内に眼科検診を受けてください。",
    "zh": "请按照上方的建议措施，在几周内进行眼科检查。",
}


def compose(choice: dict, f: Facts, lang: str) -> str:
    """선택 → 화면 문구. 형식은 예전 자유 작문과 같다: 상세 설명, <<<SUMMARY>>>, 요약 3줄."""
    lang = lang if lang in LANGS else "en"
    care_cat, closing_cat = _catalog(f)
    if f.postop:
        first = POST_ACTION[_post_kind(f)]
        line1, why1 = first["line"][lang], first["why"][lang]
    else:
        a, b = choice["exams"]
        line1 = EXAM_LINE[lang].format(a=EXAMS[a]["name"][lang], b=EXAMS[b]["name"][lang])
        why1 = EXAMS[a]["why"][lang] + " " + EXAMS[b]["why"][lang]
    care, closing = care_cat[choice["care"]], closing_cat[choice["closing"]]
    closing_line = closing["line"][lang]
    if not f.postop and f.triage == "weeks" and choice["closing"] != "visit_weeks":
        closing_line = f"{WEEKS_LEAD[lang]} {closing_line}"
    lines = [line1, care["line"][lang], closing_line]
    detail = "\n".join([
        f"{line1} {why1}",
        f"{care['line'][lang]} {care['why'][lang]}",
        f"{closing_line} {closing['why'][lang]}",
    ])
    return detail + "\n<<<SUMMARY>>>\n" + "\n".join(lines)
