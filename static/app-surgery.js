// Postoperative symptom review; not a recovery or complication diagnosis.
// Sources: https://www.moorfields.nhs.uk/for-patients/plan-your-visit/aftercare
// https://www.nhs.uk/symptoms/floaters-and-flashes-in-the-eyes/
const surgeryCopy = {
 ko: {
  surgery_entry: '수술 후 상태 확인하기', surgery_type_q: '가장 최근에 어떤 눈 수술을 받으셨나요?',
  surgery_eye_q: '가장 최근에 수술한 눈은 어느 쪽인가요?', surgery_sym_eye_q: '현재 불편한 눈은 어느 쪽인가요?',
  surgery_type_cataract: '백내장·인공수정체', surgery_type_laser: '라식·라섹 등 시력교정', surgery_type_other: '망막·녹내장·기타', surgery_type_unknown: '잘 모르겠어요',
  surgery_eye_left: '왼쪽', surgery_eye_right: '오른쪽', surgery_eye_both: '양쪽', surgery_eye_none: '불편함 없음',
  q_post_day1: '수술을 받은 지 하루가 지났나요?',
  q_post_pain: '어느 쪽 눈이든 지금 심한 통증이 있거나 통증이 점점 심해지고 있나요?',
  q_post_vision: '시력이 새로 떨어지거나, 좋아졌다가 다시 흐려지는 등 악화되고 있나요?',
  q_post_redness: '충혈·붓기나 끈적한 분비물이 새로 생기거나 점점 심해지고 있나요?',
  q_post_flashes: '번쩍이는 빛, 갑자기 늘어난 날파리 같은 점, 커튼 같은 시야 가림이 새로 생겼나요?',
  q_post_glare: '현재 빛 번짐이나 눈부심이 있나요?',
  q_post_worse: '수술 후 시간이 지나도 눈부심이나 불편함이 좋아지지 않거나, 오히려 심해지고 있나요?',
  q_post_followup: '퇴원 안내와 다음 진료 일정을 알고 있으며 그대로 따를 수 있나요?',
  sym_post_day1: '수술 당일(하루 미만)',
  sym_post_pain: '심하거나 악화되는 눈 통증', sym_post_vision: '새롭거나 악화되는 시력 변화',
  sym_post_redness: '새롭거나 악화되는 충혈·분비물', sym_post_flashes: '새로운 광시증·비문증·시야 가림',
  sym_post_glare: '눈부심·빛 번짐', sym_post_worse: '좋아지지 않거나 심해지는 불편함', sym_post_followup: '퇴원 안내·추적 진료 확인 필요',
  post_eye_operated: '수술한 눈', post_eye_affected: '불편한 눈',
  find_post_context: '확인된 수술 정보: {items}',
  rep_l1_postop: '1. 사진 판독 (수술 후에는 적용하지 않음)',
  post_limit: '수술 후 상태 확인 문진입니다. 사진이나 이 문진만으로 정상 회복·합병증 여부를 판정할 수 없습니다.',
  post_urgent: '지금 수술 병원이나 응급 안과에 연락하세요',
  post_urgent_why: '새롭거나 악화되는 위험 신호에 답하셨습니다. 연락이 닿지 않으면 응급실에서 확인받으세요. AI 설명을 기다리지 마세요.',
  post_contact: '수술 병원에 증상을 문의하세요', post_contact_why: '증상과 시작 시점을 수술 병원에 알려 확인받으세요. 예약일까지 기다려도 되는지는 담당 의료진에게 확인하세요.',
  post_follow: '수술 병원의 안내와 예정된 진료를 따르세요', post_follow_why: '이번 문진에서 위험 신호를 보고하지 않았습니다. 정상 회복을 확인한 것은 아닙니다. 새로운 증상이나 악화가 생기면 바로 문의하세요.'
 },
 en: {
  surgery_entry:'Check symptoms after eye surgery', surgery_type_q:'What was your most recent eye surgery?',
  surgery_eye_q:'Which eye was most recently operated on?', surgery_sym_eye_q:'Which eye feels uncomfortable now?',
  surgery_type_cataract:'Cataract / lens', surgery_type_laser:'Laser vision correction', surgery_type_other:'Retina / glaucoma / other', surgery_type_unknown:'Not sure',
  surgery_eye_left:'Left', surgery_eye_right:'Right', surgery_eye_both:'Both', surgery_eye_none:'No discomfort',
  q_post_day1:'Has at least one day passed since the surgery?',
  q_post_pain:'Is either eye severely painful or becoming more painful?',
  q_post_vision:'Is vision newly worse, or getting worse again after improving?',
  q_post_redness:'Is redness, swelling or sticky discharge new or increasing?',
  q_post_flashes:'Do you have new flashes, a sudden increase in floaters, or a curtain over your vision?',
  q_post_glare:'Do you currently have glare or light scatter?',
  q_post_worse:'Is glare or discomfort failing to improve over time, or getting worse?',
  q_post_followup:'Do you understand and can you follow your discharge instructions and follow-up schedule?',
  sym_post_day1:'Same day as surgery (under 24 h)',sym_post_pain:'Severe or worsening eye pain',sym_post_vision:'New or worsening vision change',sym_post_redness:'New or increasing redness / discharge',sym_post_flashes:'New flashes / floaters / curtain',sym_post_glare:'Glare / light scatter',sym_post_worse:'Discomfort not improving or worsening',sym_post_followup:'Aftercare / follow-up needs clarification',
  post_eye_operated:'operated eye', post_eye_affected:'affected eye',
  find_post_context:'Reported surgery details: {items}',
  rep_l1_postop:'1. Photo analysis (not applied after surgery)',
  post_limit:'Postoperative symptom review. Photos and this questionnaire cannot confirm normal healing or exclude complications.',
  post_urgent:'Contact your surgical team or emergency eye service now',post_urgent_why:'You reported a new or worsening warning sign. If you cannot reach them, seek emergency care. Do not wait for AI advice.',
  post_contact:'Contact your surgical team about symptoms',post_contact_why:'Describe your symptoms and when they started. Ask your team whether you can wait until your scheduled review.',
  post_follow:'Follow your surgical team’s aftercare and review schedule',post_follow_why:'No warning signs were reported in this questionnaire. This does not confirm normal healing. Contact your team if symptoms appear or worsen.'
 }
};
Object.assign(surgeryCopy, {
  "es": {
    "post_eye_operated": "ojo operado",
    "post_eye_affected": "ojo con molestias",
    "find_post_context": "Datos de la cirugía indicados: {items}",
    "rep_l1_postop": "1. Análisis de la foto (no aplicable tras la cirugía)",
    "surgery_entry": "Comprobar síntomas después de la cirugía ocular",
    "surgery_type_q": "¿Cuál fue su cirugía ocular más reciente?",
    "surgery_eye_q": "¿Qué ojo se operó más recientemente?",
    "surgery_sym_eye_q": "¿En qué ojo siente molestias ahora?",
    "surgery_type_cataract": "Cataratas / lente intraocular",
    "surgery_type_laser": "Corrección visual con láser",
    "surgery_type_other": "Retina / glaucoma / otra",
    "surgery_type_unknown": "No estoy seguro/a",
    "surgery_eye_left": "Izquierdo",
    "surgery_eye_right": "Derecho",
    "surgery_eye_both": "Ambos",
    "surgery_eye_none": "Sin molestias",
    "q_post_day1": "¿Ha pasado al menos un día desde la cirugía?",
    "q_post_pain": "¿Tiene dolor intenso o cada vez mayor en alguno de los ojos?",
    "q_post_vision": "¿Ha empeorado su visión recientemente o ha vuelto a empeorar tras mejorar?",
    "q_post_redness": "¿Tiene enrojecimiento, hinchazón o secreción pegajosa nuevos o crecientes?",
    "q_post_flashes": "¿Tiene destellos nuevos, un aumento repentino de puntos flotantes o una cortina en la visión?",
    "q_post_glare": "¿Tiene deslumbramiento o dispersión de la luz?",
    "q_post_worse": "¿El deslumbramiento o la molestia no mejora con el tiempo o está empeorando?",
    "q_post_followup": "¿Comprende y puede seguir las instrucciones de alta y las citas de seguimiento?",
    "sym_post_day1": "El mismo día de la cirugía (menos de 24 h)",
    "sym_post_pain": "Dolor ocular intenso o creciente",
    "sym_post_vision": "Cambio visual nuevo o creciente",
    "sym_post_redness": "Enrojecimiento / secreción nuevos o crecientes",
    "sym_post_flashes": "Destellos / puntos flotantes / cortina nuevos",
    "sym_post_glare": "Deslumbramiento / dispersión de luz",
    "sym_post_worse": "Molestia que no mejora o empeora",
    "sym_post_followup": "Debe aclarar los cuidados o el seguimiento",
    "post_limit": "Revisión de síntomas posoperatorios. Las fotos y este cuestionario no confirman una recuperación normal ni descartan complicaciones.",
    "post_urgent": "Contacte ahora con su equipo quirúrgico o urgencias oftalmológicas",
    "post_urgent_why": "Ha indicado una señal de alarma nueva o creciente. Si no logra contactar, acuda a urgencias. No espere la explicación de la IA.",
    "post_contact": "Consulte sus síntomas con su equipo quirúrgico",
    "post_contact_why": "Explique los síntomas y cuándo comenzaron. Pregunte al equipo si puede esperar hasta la cita programada.",
    "post_follow": "Siga los cuidados y las citas indicados por su equipo quirúrgico",
    "post_follow_why": "No ha indicado señales de alarma en este cuestionario. Esto no confirma una recuperación normal. Contacte si aparecen o empeoran síntomas."
  },
  "fr": {
    "post_eye_operated": "œil opéré",
    "post_eye_affected": "œil gênant",
    "find_post_context": "Informations sur l’opération : {items}",
    "rep_l1_postop": "1. Analyse de la photo (non applicable après l’opération)",
    "surgery_entry": "Vérifier les symptômes après une opération des yeux",
    "surgery_type_q": "Quelle a été votre dernière opération des yeux ?",
    "surgery_eye_q": "Quel œil a été opéré le plus récemment ?",
    "surgery_sym_eye_q": "Quel œil vous gêne actuellement ?",
    "surgery_type_cataract": "Cataracte / implant",
    "surgery_type_laser": "Correction de la vision au laser",
    "surgery_type_other": "Rétine / glaucome / autre",
    "surgery_type_unknown": "Je ne sais pas",
    "surgery_eye_left": "Gauche",
    "surgery_eye_right": "Droit",
    "surgery_eye_both": "Les deux",
    "surgery_eye_none": "Aucune gêne",
    "q_post_day1": "Au moins un jour s’est-il écoulé depuis l’opération ?",
    "q_post_pain": "Avez-vous une douleur intense ou croissante dans un œil ?",
    "q_post_vision": "Votre vision s’est-elle récemment dégradée ou se dégrade-t-elle après une amélioration ?",
    "q_post_redness": "Une rougeur, un gonflement ou des sécrétions collantes sont-ils apparus ou augmentent-ils ?",
    "q_post_flashes": "Avez-vous de nouveaux éclairs, une augmentation soudaine des corps flottants ou un voile comme un rideau ?",
    "q_post_glare": "Avez-vous actuellement des éblouissements ou une diffusion de la lumière ?",
    "q_post_worse": "L’éblouissement ou la gêne ne s’améliore-t-il pas avec le temps, ou s’aggrave-t-il ?",
    "q_post_followup": "Comprenez-vous et pouvez-vous suivre les consignes de sortie et le calendrier de suivi ?",
    "sym_post_day1": "Le jour même de l’opération (moins de 24 h)",
    "sym_post_pain": "Douleur oculaire intense ou croissante",
    "sym_post_vision": "Baisse visuelle nouvelle ou croissante",
    "sym_post_redness": "Rougeur / sécrétions nouvelles ou croissantes",
    "sym_post_flashes": "Nouveaux éclairs / corps flottants / rideau",
    "sym_post_glare": "Éblouissement / diffusion lumineuse",
    "sym_post_worse": "Gêne qui ne s’améliore pas ou s’aggrave",
    "sym_post_followup": "Consignes de soins / suivi à clarifier",
    "post_limit": "Questionnaire postopératoire. Les photos et ce questionnaire ne permettent ni de confirmer une guérison normale ni d’exclure des complications.",
    "post_urgent": "Contactez maintenant l’équipe chirurgicale ou les urgences ophtalmologiques",
    "post_urgent_why": "Vous avez signalé un signe d’alerte nouveau ou croissant. Si l’équipe est injoignable, allez aux urgences. N’attendez pas l’avis de l’IA.",
    "post_contact": "Contactez l’équipe chirurgicale au sujet de vos symptômes",
    "post_contact_why": "Décrivez vos symptômes et leur début. Demandez à l’équipe si vous pouvez attendre le rendez-vous prévu.",
    "post_follow": "Suivez les consignes de soins et de suivi de votre équipe chirurgicale",
    "post_follow_why": "Aucun signe d’alerte n’a été signalé dans ce questionnaire. Cela ne confirme pas une guérison normale. Contactez l’équipe si des symptômes apparaissent ou s’aggravent."
  },
  "ja": {
    "post_eye_operated": "手術した目",
    "post_eye_affected": "不快感のある目",
    "find_post_context": "確認された手術情報: {items}",
    "rep_l1_postop": "1. 写真判読（術後は適用しません）",
    "surgery_entry": "手術後の症状を確認する",
    "surgery_type_q": "直近に受けた目の手術は何ですか？",
    "surgery_eye_q": "直近に手術した目はどちらですか？",
    "surgery_sym_eye_q": "今、不快感がある目はどちらですか？",
    "surgery_type_cataract": "白内障・眼内レンズ",
    "surgery_type_laser": "レーシックなどの視力矯正",
    "surgery_type_other": "網膜・緑内障・その他",
    "surgery_type_unknown": "わかりません",
    "surgery_eye_left": "左目",
    "surgery_eye_right": "右目",
    "surgery_eye_both": "両目",
    "surgery_eye_none": "不快感なし",
    "q_post_day1": "手術から1日以上たちましたか？",
    "q_post_pain": "どちらかの目に強い痛み、または悪化する痛みがありますか？",
    "q_post_vision": "新たな視力低下や、一度改善した後に再び見えにくくなるなどの悪化がありますか？",
    "q_post_redness": "充血・腫れ・粘りのある目やにが新たに出た、または増えていますか？",
    "q_post_flashes": "光が走る、浮遊物が急に増える、カーテンのように視野が遮られる症状が新たにありますか？",
    "q_post_glare": "今、光のにじみやまぶしさがありますか？",
    "q_post_worse": "時間がたっても、まぶしさや不快感が改善しない、または悪化していますか？",
    "q_post_followup": "退院時の説明と次回の受診予定を理解し、そのとおりに対応できますか？",
    "sym_post_day1": "手術当日（24時間未満）",
    "sym_post_pain": "強い、または悪化する目の痛み",
    "sym_post_vision": "新たな、または悪化する見え方の変化",
    "sym_post_redness": "新たな、または悪化する充血・目やに",
    "sym_post_flashes": "新たな光視症・飛蚊症・視野の遮り",
    "sym_post_glare": "まぶしさ・光のにじみ",
    "sym_post_worse": "改善しない・悪化する不快感",
    "sym_post_followup": "退院後のケア・受診予定の確認が必要",
    "post_limit": "手術後の症状を確認する問診です。写真やこの問診だけでは正常な回復を確認したり、合併症を否定したりできません。",
    "post_urgent": "今すぐ手術を受けた医療機関か眼科救急に連絡してください",
    "post_urgent_why": "新たな、または悪化する警告症状が報告されました。連絡がつかなければ救急を受診してください。AIの説明を待たないでください。",
    "post_contact": "手術を受けた医療機関に症状を相談してください",
    "post_contact_why": "症状と始まった時期を伝えてください。予約日まで待てるかは担当の医療者に確認してください。",
    "post_follow": "手術を受けた医療機関の指示と受診予定に従ってください",
    "post_follow_why": "今回の問診で警告症状の報告はありませんでした。正常な回復を確認したわけではありません。症状が出たり悪化したらすぐに相談してください。"
  },
  "zh": {
    "post_eye_operated": "手术眼",
    "post_eye_affected": "不适眼",
    "find_post_context": "已确认的手术信息：{items}",
    "rep_l1_postop": "1. 照片判读（术后不适用）",
    "surgery_entry": "检查眼部术后症状",
    "surgery_type_q": "您最近接受了哪种眼部手术？",
    "surgery_eye_q": "最近做手术的是哪只眼？",
    "surgery_sym_eye_q": "目前哪只眼感到不适？",
    "surgery_type_cataract": "白内障 / 人工晶状体",
    "surgery_type_laser": "激光视力矫正",
    "surgery_type_other": "视网膜 / 青光眼 / 其他",
    "surgery_type_unknown": "不清楚",
    "surgery_eye_left": "左眼",
    "surgery_eye_right": "右眼",
    "surgery_eye_both": "双眼",
    "surgery_eye_none": "没有不适",
    "q_post_day1": "手术已经过了一天以上吗？",
    "q_post_pain": "任一眼是否有剧烈或逐渐加重的疼痛？",
    "q_post_vision": "是否新出现视力下降，或好转后再次变得模糊？",
    "q_post_redness": "是否新出现或加重的充血、肿胀或黏性分泌物？",
    "q_post_flashes": "是否新出现闪光、飞蚊突然增多或幕帘样视野遮挡？",
    "q_post_glare": "目前是否有眩光或光线散射？",
    "q_post_worse": "随着时间推移，眩光或不适是否没有改善，甚至加重？",
    "q_post_followup": "您是否理解并能遵循出院指导和复诊安排？",
    "sym_post_day1": "手术当天（不足24小时）",
    "sym_post_pain": "剧烈或加重的眼痛",
    "sym_post_vision": "新出现或加重的视力变化",
    "sym_post_redness": "新出现或加重的充血 / 分泌物",
    "sym_post_flashes": "新出现闪光 / 飞蚊 / 幕帘样遮挡",
    "sym_post_glare": "眩光 / 光线散射",
    "sym_post_worse": "未改善或加重的不适",
    "sym_post_followup": "需要确认术后护理 / 复诊安排",
    "post_limit": "这是术后症状问卷。照片或本问卷不能确认恢复正常，也不能排除并发症。",
    "post_urgent": "请立即联系手术医疗团队或眼科急诊",
    "post_urgent_why": "您报告了新出现或加重的警示症状。如无法联系，请前往急诊。不要等待AI解释。",
    "post_contact": "请向手术医疗团队咨询症状",
    "post_contact_why": "请说明症状及开始时间。能否等到预约复诊，请向负责您的医疗人员确认。",
    "post_follow": "请遵循手术医疗团队的护理指导和复诊安排",
    "post_follow_why": "本问卷中未报告警示症状，但这不代表已确认恢复正常。如出现新症状或症状加重，请立即联系医疗团队。"
  }
});
Object.keys(translations).forEach(lang => Object.assign(translations[lang], surgeryCopy[lang]));
// 술후 전용 문진으로 갈아타는 조건 — 수술 4주 이내만이다.
//
// 'past'(4주 초과)까지 넣으면 10년 전 라식 한 번으로 나이·당뇨·고혈압·가족력·흡연
// 문항과 급성 녹내장(rf_acute)·갑작스러운 시력저하(rf_sudden) 적신호가 통째로
// 사라지고, 사진 AI가 백내장 위험을 잡아도 '수술 병원에 문의'로 안내가 바뀐다.
// 오래된 수술 이력은 일반 검진을 그대로 받고, 적신호 3개만 얹는다
// (data.js의 surgery_pain·surgery_vision·surgery_redness).
function hasSurgery() { return ['today','recent'].includes(state.riskAnswers?.surgery); }
// 이 회차에 '실제 사진 판독 결과'가 있는가.
//
// 'postop'(수술 후 입구)과 'skipped'(사진 없이 증상 확인)는 사진을 한 장도 받지 않은
// 상태 표시다. 이 둘을 아래 '판독 제외'에 함께 묶으면, 올린 적도 없는 사진을 두고
// "인공수정체 때문에 사진 판독을 적용하지 않습니다"라고 설명하게 된다 —
// 수술 후 입구에서 '4주보다 이전'을 고른 경로에서 그대로 재현됐다(라식이라고 답해도
// '인공수정체'라고 말했다). 제외 판단은 판독 결과가 있을 때만 의미가 있다.
const PHOTO_VERDICTS = ['risk', 'borderline', 'uncertain', 'normal'];
function hasPhotoVerdict() { return PHOTO_VERDICTS.includes(state.aiResultCode); }
// ------------------------------------------------------------------
// 한쪽 눈만 수술한 사람의 '반대쪽(수술하지 않은) 눈'은 판독할 수 있다.
//
// 왜 살릴 가치가 있는가: 백내장 수술을 한쪽 받은 사람은 대개 65세 이상이고, 남은
// 자연 수정체 눈이 백내장으로 진행할 확률이 평균보다 높다. 이 사람들에게 스크리닝을
// 통째로 막으면 가장 필요한 대상에게서 기능을 빼앗는다.
//
// 왜 좌우를 쓰지 않는가: vision.py의 eyes[].side는 '사진 x좌표' 기준이다
// (eye_detector.py가 x좌표로 정렬한다). 셀카는 기기·설정에 따라 거울상으로 저장되므로
// 사진의 왼쪽 눈이 해부학적 왼눈인지 알 수 없다. 그래서 좌우 매핑에는 절대 의존하지 않는다.
//
// 대신 좌우와 무관하게 성립하는 규칙을 쓴다:
//   두 눈 크롭의 판정이 서로 같으면, 수술하지 않은 눈이 둘 중 어느 쪽이든 그 판정이다.
// 판정이 갈리면 위험 신호가 인공수정체(반사) 때문인지 진짜 혼탁인지 구분할 수 없으므로
// 종전대로 판독 전체를 버린다.
/** 사진이 두 눈을 함께 담았고, 두 눈의 판정이 일치하는가. */
function bothEyesAgree() {
 const eyes = state.aiResultData?.eyes;
 return !!state.aiResultData?.twoEyes && Array.isArray(eyes) && eyes.length === 2
  && eyes.every(e => e && e.side !== 'single') && eyes[0].code === eyes[1].code;
}
/** '수술한 눈이 한쪽인가'를 물을 가치가 있는가.
 *  답이 판정을 바꿀 수 없으면(단안 클로즈업, 두 눈 판정 불일치, 애초에 인공수정체가
 *  아님) 묻지 않는다. 시기와 무관하게 성립한다 — 어제 한쪽을 수술했어도 반대쪽
 *  자연 수정체 눈은 그대로 판독할 수 있다. */
function fellowEyeQuestionApplies() {
 return lensStatus() === 'yes' && bothEyesAgree();
}
/** 수술하지 않은 반대쪽 눈의 판독을 그대로 쓸 수 있는가.
 *  'both'(양쪽 수술)·'unknown'(모르겠음)은 살릴 눈이 없거나 확신할 수 없으므로 제외한다. */
function fellowEyeAssessable() {
 return hasPhotoVerdict()
  && state.riskAnswers?.surgery_both === 'one'
  && fellowEyeQuestionApplies();
}
/** 이 사람의 눈에 인공수정체가 들어 있는가 — 사진 판독을 적용할 수 있는지를 가르는 기준.
 *
 *  왜 '수술을 받았는가'가 아니라 '수정체를 바꿨는가'인가:
 *  모델은 자연 수정체 눈 사진으로 학습했다. 인공수정체(IOL)는 겉보기와 반사가 달라
 *  판독이 뒤집힌다 — 2026-09-13 Commons 인공수정체 눈 사진(자유 라이선스, 측정 전용)을
 *  실제 판독에 넣었더니 수술 중이 아닌 겉사진 2장이 risk 100·uncertain, 수술 현미경
 *  사진 5장 중 3장이 risk였다(표본이 작아 방향만 확인한 것이다).
 *  반대로 라식·라섹은 각막만 깎고 수정체를 건드리지 않으므로 판독의 근거가 그대로 남는다.
 *  망막·녹내장 수술도 수정체 자체를 바꾸지는 않지만, 유리체절제술에 백내장 수술을 함께
 *  하는 경우가 흔해 '인공수정체 이력'을 따로 확인한 뒤에만 판독을 적용한다.
 *
 *  예전에는 '수술한 적 있음' 하나로 전부 막았다. 그래서 12년 전 라식을 받은 사람과
 *  어제 라섹을 받은 사람의 백내장 스크리닝이 통째로 사라졌다 — 수정체는 멀쩡한데도. */
function lensStatus() {
 const a = state.riskAnswers || {};
 // 시기를 아직 답하지 않았어도 게이트에서 '예'라고 했으면 수술 이력이 있는 것이다.
 const operated = state.hadSurgery === true || (a.surgery && a.surgery !== 'none');
 if (!operated) return 'no';
 if (a.surgery_type === 'cataract' || a.surgery_lens_history === 'yes') return 'yes';
 if (a.surgery_lens_history === 'no') return 'no';
 // 종류를 아직 안 물었거나 '모르겠어요'라면 인공수정체 가능성을 배제할 수 없다.
 return 'unknown';
}
/** 수술 이력 문항 중 판독 적용 여부를 가르는 답이 아직 남아 있는가.
 *  남아 있는 동안에는 점수·판정을 보여주지 않는다(나중에 취소해야 할 수도 있으므로). */
function surgeryHistoryPending() {
 const a = state.riskAnswers || {};
 if (state.hadSurgery === false || a.surgery === 'none') return false;
 if (a.surgery === undefined) return true;   // 수술은 했는데 시기를 아직 묻지 않았다
 if (a.surgery_type === undefined) return true;
 if (a.surgery_type !== 'cataract' && a.surgery_lens_history === undefined) return true;
 return fellowEyeQuestionApplies() && a.surgery_both === undefined;
}
// The upload has no reliable anatomical side. Do not apply its cataract score
// to an eye with an artificial lens, or when the lens status is unknown.
function photoAssessmentExcluded() {
 if (!hasPhotoVerdict()) return false;
 return lensStatus() !== 'no' && !fellowEyeAssessable();
}
/** 수정체를 건드리지 않은 수술이라 판독을 그대로 적용한 경우.
 *  수술 직후에는 각막 부종으로 값이 달라질 수 있어, 그 사실을 함께 말해야 한다. */
function photoAppliesDespiteSurgery() {
 // 반대쪽 눈만 판독하는 경우에는 수술한 눈의 수정체가 실제로 교체됐다.
 // '판독을 적용함'과 '수정체를 교체하지 않음'은 같은 조건이 아니다.
 return hasPhotoVerdict() && hasSurgery() && lensStatus() === 'no';
}
function effectiveCataractCode() {
 // 사진을 한 장도 받지 않은 회차는 판독 자체가 없다.
 if (state.aiResultCode === 'postop' || !hasPhotoVerdict()) return state.aiResultCode;
 return photoAssessmentExcluded() ? 'excluded' : state.aiResultCode;
}
// ------------------------------------------------------------------
// 수술 여부 확인(step-surgery) — 검사의 첫 갈림길.
//
// 왜 사진보다 먼저 묻는가: 인공수정체가 들어간 눈은 사진 판독 대상이 아니고(모델 학습
// 분포 밖이라 겉사진이 risk로 뒤집힌다 — 위 lensStatus() 주석의 2026-09-13 실측),
// 4주 이내 수술이면 문진도 술후 전용 문항으로 통째로 바뀐다. 예전에는 문진 첫 문항으로
// 물어서, 수술한 사람도 일반 촬영 가이드와 백내장 판정 화면을 먼저 다 보고 나서야
// '이 판독은 적용하지 않습니다'를 읽었다.
const surgeryGateCopy = {
 ko: ['어떤 검사로 시작할까요?', '질환 때문에 눈 수술을 받은 적이 있으면 수술 맞춤 검사로, 그렇지 않으면 일반 눈 건강 검사로 안내합니다.',
  '질환 때문에 눈 수술을 받았어요', '수술 맞춤 검사', '질환 관련 수술은 없어요', '일반 눈 건강 검사',
  '언제 수술을 받으셨나요?',
  '수술한 분께 드리는 촬영 안내',
  '<li>의료용 안대·보호대는 그대로 두세요. 사진을 찍으려고 벗기지 마세요.</li><li>눈을 만지거나 억지로 크게 뜨지 마세요.</li><li>촬영이 어려우면 사진을 건너뛰고 다음 단계로 가세요.</li>',
  '사진 없이 다음 단계로',
  '수정체를 건드리지 않은 수술이라 사진 판독을 그대로 적용했습니다. 다만 수술 직후에는 각막이 붓거나 흐려 판독이 달라질 수 있습니다.'],
 en: ['Which screening should you start?', 'If you had eye surgery because of an eye condition, we will match the screening to it. Otherwise, use the standard eye screening.',
  'I had surgery for an eye condition', 'Screening matched to surgery', 'No surgery for an eye condition', 'Standard eye screening',
  'When was the surgery?',
  'If you have had eye surgery',
  '<li>Leave any medical patch or shield in place. Never remove it for a photo.</li><li>Do not touch the eye or force it open.</li><li>If a photo is difficult, skip it and continue.</li>',
  'Continue without a photo',
  'This surgery did not replace the lens, so the photo reading still applies. Just after surgery the cornea can be swollen or hazy, which may change the reading.'],
 es: ['¿Con qué revisión desea comenzar?', 'Si tuvo una cirugía ocular por una enfermedad, adaptaremos la revisión. Si no, usaremos la revisión ocular estándar.',
  'Me operaron por una enfermedad ocular', 'Revisión adaptada a la cirugía', 'No me operaron por una enfermedad ocular', 'Revisión ocular estándar',
  '¿Cuándo fue la cirugía?',
  'Si ha tenido una cirugía ocular',
  '<li>Deje puesto el parche o protector médico. No lo retire para la foto.</li><li>No se toque el ojo ni lo abra a la fuerza.</li><li>Si le cuesta, omita la foto y continúe.</li>',
  'Continuar sin foto',
  'Esta cirugía no sustituyó el cristalino, así que la lectura de la foto sigue siendo válida. Justo después de operar, la córnea puede estar inflamada y alterar el resultado.'],
 fr: ['Par quel dépistage souhaitez-vous commencer ?', 'Si vous avez été opéré pour une maladie oculaire, nous adapterons le dépistage. Sinon, nous utiliserons le dépistage standard.',
  'J’ai été opéré pour une maladie oculaire', 'Dépistage adapté à l’opération', 'Je n’ai pas été opéré pour une maladie oculaire', 'Dépistage oculaire standard',
  'Quand avez-vous été opéré ?',
  'Si vous avez été opéré',
  '<li>Laissez en place le pansement ou la coque de protection. Ne l’enlevez jamais pour la photo.</li><li>Ne touchez pas l’œil et ne le forcez pas à s’ouvrir.</li><li>Si la photo est difficile, passez-la et continuez.</li>',
  'Continuer sans photo',
  'Cette opération n’a pas remplacé le cristallin : la lecture de la photo reste valable. Juste après l’opération, la cornée peut être gonflée ou trouble et modifier le résultat.'],
 ja: ['どの検査から始めますか？', '目の病気で手術を受けた場合は手術に合わせた検査を、それ以外は通常の目の健康チェックをご案内します。',
  '目の病気で手術を受けました', '手術に合わせた検査', '目の病気の手術はありません', '通常の目の健康チェック',
  'いつ手術を受けましたか？',
  '手術を受けた方へ',
  '<li>医療用の眼帯・保護具はそのままにしてください。撮影のために外さないでください。</li><li>目に触れたり、無理に大きく開けたりしないでください。</li><li>撮影が難しければ写真を飛ばして次へ進んでください。</li>',
  '写真なしで次へ',
  '水晶体を入れ替えていない手術のため、写真判読をそのまま適用しました。ただし術直後は角膜がむくんだり濁ったりして判読が変わることがあります。'],
 zh: ['您想从哪种检查开始？', '如果因眼病做过手术，我们会安排相应检查；否则进行常规眼部健康检查。',
  '因眼病做过手术', '按手术情况检查', '没有因眼病做过手术', '常规眼部健康检查',
  '什么时候做的手术？',
  '做过眼部手术的用户请注意',
  '<li>请保留医用眼罩或护罩，不要为拍照而摘下。</li><li>不要触碰眼睛，也不要强行睁大。</li><li>如果拍照困难，可跳过照片继续下一步。</li>',
  '不拍照，继续下一步',
  '本次手术未更换晶状体，因此照片判读仍然适用。但术后初期角膜可能水肿或混浊，判读结果可能受影响。']
};
for (const [lang, copy] of Object.entries(surgeryGateCopy)) {
 ['gate_title','gate_desc','gate_d_yes','gate_d_yes_sub','gate_d_none','gate_d_none_sub','gate_when_q',
  'post_photo_title','post_photo_tips','post_skip_photo',
  'photo_lens_intact'].forEach((key,i)=>translations[lang][key]=copy[i]);
}
Object.assign(translations.ko, { post_guide_title:'수술한 분을 위한 검사 안내', post_guide_body:'수술 시기와 종류에 따라 사진 검사 방법이 달라질 수 있어요. 다음 문진에서 먼저 확인합니다. 사진이 어렵거나 보호대를 하고 있다면 사진을 찍지 않고 진행할 수 있습니다.', post_photo_continue:'사진으로 진행하기', post_photo_upload_title:'수술 관련 사진 검사', post_camera_btn:'수술 관련 사진 촬영' });
Object.assign(translations.en, { post_guide_title:'Screening after eye surgery', post_guide_body:'The photo check may differ depending on when and what kind of surgery you had. We will ask first. If taking a photo is difficult or you are wearing a shield, you can continue without one.', post_photo_continue:'Continue with a photo', post_photo_upload_title:'Surgery-related photo check', post_camera_btn:'Take a surgery-related photo' });
Object.assign(translations.es, { post_guide_title:'Prueba después de una cirugía ocular', post_guide_body:'La prueba con foto puede variar según cuándo y qué cirugía tuvo. Primero se lo preguntaremos. Si es difícil hacer una foto o lleva un protector, puede continuar sin ella.', post_photo_continue:'Continuar con una foto', post_photo_upload_title:'Foto relacionada con la cirugía', post_camera_btn:'Tomar foto relacionada con la cirugía' });
Object.assign(translations.fr, { post_guide_title:'Dépistage après une opération des yeux', post_guide_body:'L’analyse photo peut changer selon la date et le type d’opération. Nous vous le demanderons d’abord. Si la photo est difficile ou si vous portez une coque, vous pouvez continuer sans photo.', post_photo_continue:'Continuer avec une photo', post_photo_upload_title:'Photo liée à l’opération', post_camera_btn:'Prendre une photo liée à l’opération' });
Object.assign(translations.ja, { post_guide_title:'手術を受けた方の検査案内', post_guide_body:'写真検査は手術の時期や種類によって変わることがあります。まず問診で確認します。撮影が難しい場合や保護具を付けている場合は、写真なしで続けられます。', post_photo_continue:'写真で進む', post_photo_upload_title:'手術に関する写真検査', post_camera_btn:'手術に関する写真を撮る' });
Object.assign(translations.zh, { post_guide_title:'做过眼部手术的用户检查指南', post_guide_body:'照片检查方式可能因手术时间和类型而不同。我们会先询问。如果拍照困难或正在佩戴护罩，可以不拍照继续检查。', post_photo_continue:'使用照片继续', post_photo_upload_title:'手术相关照片检查', post_camera_btn:'拍摄手术相关照片' });

// Entry records actual surgery history, not the user's guess about its cause.
// Both disease-related and other surgery must reach the timing/type questions.
const surgeryEntryCopy = {
 ko: ['눈 수술을 받은 적이 있나요?', '백내장 등 질환 수술뿐 아니라 라식·라섹, 다쳐서 받은 눈 수술도 포함해 주세요.', '눈 수술을 받았어요', '눈 수술을 받은 적 없어요', '사진 검사와 격자 검사 뒤 문진에서 수술 시기와 종류를 확인합니다. 그전에는 사진 점수의 해석을 보류합니다. 촬영이 어렵거나 보호대를 착용 중이면 사진 없이 진행할 수 있어요.'],
 en: ['Have you had eye surgery?', 'Include surgery for eye conditions, LASIK/PRK and eye injuries.', 'I have had eye surgery', 'I have never had eye surgery', 'After the photo and grid checks, the questionnaire asks when and what surgery you had. Photo scores are withheld until then. You can continue without a photo if taking one is difficult or you wear a shield.'],
 es: ['¿Ha tenido cirugía ocular?', 'Incluya operaciones por enfermedades, LASIK/PRK y lesiones oculares.', 'He tenido cirugía ocular', 'Nunca he tenido cirugía ocular', 'Después de la foto y la cuadrícula, preguntaremos la fecha y el tipo de cirugía. La interpretación de la foto queda pendiente hasta entonces. Puede continuar sin foto si es difícil tomarla o usa un protector.'],
 fr: ['Avez-vous été opéré des yeux ?', 'Incluez les maladies oculaires, le LASIK/PRK et les blessures aux yeux.', 'J’ai été opéré des yeux', 'Je n’ai jamais été opéré des yeux', 'Après la photo et la grille, le questionnaire précise la date et le type d’opération. Le score photo reste en attente jusque-là. Vous pouvez continuer sans photo si elle est difficile à prendre ou si vous portez une coque.'],
 ja: ['目の手術を受けたことがありますか？', '目の病気の手術だけでなく、レーシック・PRKやけがによる手術も含めてください。', '目の手術を受けました', '目の手術は受けていません', '写真と格子のチェック後、問診で手術の時期と種類を確認します。それまでは写真スコアの解釈を保留します。撮影が難しい場合や保護具を着けている場合は、写真なしで進めます。'],
 zh: ['您做过眼部手术吗？', '请包括眼病手术、LASIK/PRK及眼外伤手术。', '做过眼部手术', '从未做过眼部手术', '照片和网格检查后，问诊会确认手术时间和类型。在此之前暂不解释照片分数。拍照困难或佩戴护罩时，可不拍照继续。']
};
for (const [lang, copy] of Object.entries(surgeryEntryCopy)) {
 ['gate_title','gate_desc','gate_d_yes','gate_d_none','post_guide_body'].forEach((key, i) => translations[lang][key] = copy[i]);
}

/** 첫 화면의 시작 버튼 — 촬영이 아니라 수술 여부 확인으로 간다. */
function startScreening() {
 state.hadSurgery = null;    // 초기화가 이 값을 읽는다 — 먼저 비운다
 state.gateAnswers = {};
 resetScreeningState();
 applyTrack();
 showTab('tab-test'); nextStep('step-surgery');
}

/** 시작 전 단 하나의 질문: 원인과 무관하게 눈 수술을 받은 적이 있는가.
 *
 *  시기·종류·인공수정체 이력은 여기서 묻지 않고 문진에서 이어 묻는다. 시작 화면에
 *  네 화면을 세워 두면 검사를 시작하기도 전에 취조처럼 느껴진다(팀 피드백). 대신
 *  외상·시력교정 수술도 이력을 보존하며, 이 한 답으로 사진을 찍기
 *  '전에' 정해야 하는 것은 다 정해진다:
 *    · 수술 후 촬영 안내(보호대를 벗지 마세요)를 보여줄지
 *    · 안대 때문에 못 찍는 사람에게 '사진 없이 다음 단계로'를 열어줄지
 *    · 판독 적용 여부가 아직 미정이라고 결과 화면에서 밝힐지(surgeryHistoryPending)
 */
function answerSurgeryGate(hadSurgery) {
 state.hadSurgery = !!hadSurgery;
 // '아니오'만 문진 첫 문항의 답이 된다. '예'는 시기를 모르므로 문진이 이어서 묻는다.
 setGateAnswers(hadSurgery ? {} : { surgery: 'none' });
 nextStep('step-guide');
}

/** 게이트에서 받은 답을 기록한다.
 *
 *  왜 riskAnswers와 따로 두는가: 사진을 올릴 때마다 resetScreeningState()가 돌면서
 *  riskAnswers를 비운다. 게이트 답을 거기에만 두면 문진에 닿기도 전에 '수술한 눈'이라는
 *  사실이 사라져 사진 판독이 그대로 적용된다. gateAnswers가 원본이고, 초기화는 매번
 *  이 값을 riskAnswers에 다시 심는다(app-core.js의 resetScreeningState). */
function setGateAnswers(answers) {
 state.gateAnswers = answers;
 resetScreeningState();      // riskAnswers를 gateAnswers로 다시 심는다
 applyTrack();
}

/** 수술한 눈은 안대·보호대로 촬영이 불가능할 수 있다. 사진 없이 나머지 단계를 잇는다.
 *  사진을 한 장도 받지 않았다는 표시가 'postop'이다(app-surgery.js 위쪽 주석). */
function skipPhotoStep() {
 // 숨겨진 버튼이나 오래된 이벤트로 일반 사용자가 술후 회차에 들어가지 않게 한다.
 if (state.hadSurgery !== true && !hasSurgery()) return;
 cancelEyeAnalysis();
 state.aiResultCode = 'postop';
 state.aiResultData = null;
 state.photoChecks = [];
 startAmslerStep();
}

/** 수술 전용 안내·버튼을 이 회차의 경로에 맞춰 보이거나 감춘다.
 *  시기를 묻기 전이라도 게이트에서 '예'라고 했으면 보여준다 — 보호대를 벗지 말라는
 *  안내와 '사진 없이 다음 단계로'는 사진을 찍기 전에 필요하다. */
function applyTrack() {
 const surgery = state.hadSurgery === true || hasSurgery();
 document.body.dataset.track = surgery ? 'surgery' : 'general';
 document.querySelectorAll('[data-surgery-only]').forEach(el => { el.hidden = !surgery; });
 document.querySelectorAll('[data-general-only]').forEach(el => { el.hidden = surgery; });
}


const surgeryRiskQuestions = [
 ['surgery_type','surgery_type_q',['cataract','laser','other','unknown'],'surgery_type_'],
 ['surgery_eye','surgery_eye_q',['left','right','both'],'surgery_eye_'],
 ['surgery_sym_eye','surgery_sym_eye_q',['left','right','both','none'],'surgery_eye_']
].map(([code,key,values,prefix]) => ({code,key,type:'choice',options:values.map(v=>({v,key:prefix+v,score:0}))}));
// 최근 수술이 백내장이 아니어도 과거 인공수정체 이력을 놓치지 않도록 분리해 묻는다.
// '가장 최근 수술' 하나만으로는 백내장 수술 후 다른 수술을 받은 사용자를 표현할 수 없다.
const remoteLensHistoryQuestion = {
 code:'surgery_lens_history', key:'surgery_lens_history_q', type:'choice',
 options:['yes','no','unknown'].map(v=>({v,key:'surgery_lens_history_'+v,score:0}))
};

function remoteSurgeryLabels() {
 const t = translations[state.lang];
 const label = (q, value) => {
  const opt = q && q.options.find(o => o.v === value);
  return opt ? t[opt.key] : '';
 };
 // 답 라벨만 나열하면 '… · 없어요 · 잘 모르겠어요'처럼 무엇에 대한 답인지 알 수 없다.
 // 각 답 앞에 항목 이름을 붙인다(리포트와 AI 소견 입력에 그대로 쓰인다).
 const named = (name, q, value) => {
  const text = label(q, value);
  return text ? `${t[name]}: ${text}` : '';
 };
 return [
  t.surgery_past,
  named('remote_type_label', surgeryRiskQuestions[0], state.riskAnswers?.surgery_type),
  named('remote_lens_label', remoteLensHistoryQuestion, state.riskAnswers?.surgery_lens_history),
  named('remote_scope_label', remoteSurgeryScopeQuestion, state.riskAnswers?.surgery_both),
 ].filter(Boolean);
}
// 4주 초과 이력 전용 문항. surgery_eye('가장 최근에 수술한 눈')를 재사용하면 안 된다 —
// 양안 백내장 수술은 몇 주 간격으로 따로 받는 것이 일반적이라, '가장 최근은 왼쪽'이라는
// 답을 '오른쪽은 수술하지 않았다'로 읽으면 인공수정체 눈을 판독해 버린다.
// 그래서 시기를 묻지 않고 '수술받은 눈이 한쪽인가 양쪽인가'만, 문항 안에서 명시해 묻는다.
const remoteSurgeryScopeQuestion = {
 code:'surgery_both', key:'surgery_both_q', type:'choice',
 options:['one','both','unknown'].map(v=>({v,key:'surgery_both_'+v,score:0}))
};
// 'day1'이 맨 앞인 이유: 경과를 묻는 문항(worse)은 수술 당일에 물으면 안 된다. 좋아질
// 시간 자체가 없었기 때문에 정상 회복 중인 사람도 '예'가 나오고, 당연한 술후 눈부심이
// '병원에 문의하세요'로 올라간다. (예전 q_post_change는 '수술 전에는 없었나'와 '좋아지지
// 않나'를 한 문장에 묶어서, 당일 수술자는 앞 절이 항상 참이라 무조건 걸렸다.)
//
// 예전에는 이걸 시작 화면의 시기 선택지('오늘' vs '최근 4주 이내')로 갈랐다. 그런데 그 둘은
// 서로 배타적이지도 않고(오늘도 4주 이내다), 사용자에게 보이는 차이도 없이 문항 하나를
// 가르는 내부 사정일 뿐이었다. 질문은 문진에서 묻는 것이 맞다.
const postoperativeQuestions = ['day1','pain','vision','redness','flashes','glare','worse','followup'].map(kind=>({
 code:'post_'+kind,key:'q_post_'+kind,disease:'general',weight:0,
 redFlag:['pain','vision','redness','flashes'].includes(kind),
 // invert: '아니오'를 리포트에 남기는 문항. day1은 위험 신호가 아니라 맥락이다
 // (weight 0·redFlag 없음) — '수술 당일'이라는 사실이 남아야 소견이 그 시점을 안다.
 invert:['followup','day1'].includes(kind),
 ...(kind==='worse' ? {skipIf:{code:'post_day1',answer:false}} : {})
}));
function postoperativeTriage(ctx, t) {
 const urgent=(ctx.redFlags || []).length>0;
 const a=state.symptomAnswers || {};
 // 사진 판독은 적용하지 않는다. 일반 검사에서 암슬러를 끝낸 뒤 수술 이력을
 // 답할 수도 있으므로, 이미 보고된 암슬러 이상은 유지한다.
 // 퇴원 안내를 따를 수 있는지 '모른다'는 것 자체가 수술팀에 확인할 이유다.
 const contact=a.post_worse===true || a.post_followup===false || a.post_followup==='unknown' || ctx.amslerAbnormal===true;
 const kind=urgent?'urgent':contact?'contact':'follow';
 return {level:urgent?'urgent':contact?'now':'monitor',label:t['post_'+kind],
  why:t['post_'+kind+'_why'],note:t.post_limit,riskScore:0,riskMax:13};
}
