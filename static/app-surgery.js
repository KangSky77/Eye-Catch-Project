// Postoperative symptom review; not a recovery or complication diagnosis.
// Sources: https://www.moorfields.nhs.uk/for-patients/plan-your-visit/aftercare
// https://www.nhs.uk/symptoms/floaters-and-flashes-in-the-eyes/
const surgeryCopy = {
 ko: {
  surgery_entry: '수술 후 상태 확인하기', surgery_type_q: '가장 최근에 어떤 눈 수술을 받으셨나요?',
  surgery_eye_q: '가장 최근에 수술한 눈은 어느 쪽인가요?', surgery_sym_eye_q: '현재 불편한 눈은 어느 쪽인가요?',
  surgery_type_cataract: '백내장·인공수정체', surgery_type_laser: '라식·라섹 등 시력교정', surgery_type_other: '망막·녹내장·기타', surgery_type_unknown: '잘 모르겠어요',
  surgery_eye_left: '왼쪽', surgery_eye_right: '오른쪽', surgery_eye_both: '양쪽', surgery_eye_none: '불편함 없음',
  q_post_pain: '어느 쪽 눈이든 지금 심한 통증이 있거나 통증이 점점 심해지고 있나요?',
  q_post_vision: '시력이 새로 떨어지거나, 좋아졌다가 다시 흐려지는 등 악화되고 있나요?',
  q_post_redness: '충혈·붓기나 끈적한 분비물이 새로 생기거나 점점 심해지고 있나요?',
  q_post_flashes: '번쩍이는 빛, 갑자기 늘어난 날파리 같은 점, 커튼 같은 시야 가림이 새로 생겼나요?',
  q_post_glare: '현재 빛 번짐이나 눈부심이 있나요?',
  q_post_worse: '수술 후 시간이 지나도 눈부심이나 불편함이 좋아지지 않거나, 오히려 심해지고 있나요?',
  q_post_followup: '퇴원 안내와 다음 진료 일정을 알고 있으며 그대로 따를 수 있나요?',
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
  q_post_pain:'Is either eye severely painful or becoming more painful?',
  q_post_vision:'Is vision newly worse, or getting worse again after improving?',
  q_post_redness:'Is redness, swelling or sticky discharge new or increasing?',
  q_post_flashes:'Do you have new flashes, a sudden increase in floaters, or a curtain over your vision?',
  q_post_glare:'Do you currently have glare or light scatter?',
  q_post_worse:'Is glare or discomfort failing to improve over time, or getting worse?',
  q_post_followup:'Do you understand and can you follow your discharge instructions and follow-up schedule?',
  sym_post_pain:'Severe or worsening eye pain',sym_post_vision:'New or worsening vision change',sym_post_redness:'New or increasing redness / discharge',sym_post_flashes:'New flashes / floaters / curtain',sym_post_glare:'Glare / light scatter',sym_post_worse:'Discomfort not improving or worsening',sym_post_followup:'Aftercare / follow-up needs clarification',
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
    "q_post_pain": "¿Tiene dolor intenso o cada vez mayor en alguno de los ojos?",
    "q_post_vision": "¿Ha empeorado su visión recientemente o ha vuelto a empeorar tras mejorar?",
    "q_post_redness": "¿Tiene enrojecimiento, hinchazón o secreción pegajosa nuevos o crecientes?",
    "q_post_flashes": "¿Tiene destellos nuevos, un aumento repentino de puntos flotantes o una cortina en la visión?",
    "q_post_glare": "¿Tiene deslumbramiento o dispersión de la luz?",
    "q_post_worse": "¿El deslumbramiento o la molestia no mejora con el tiempo o está empeorando?",
    "q_post_followup": "¿Comprende y puede seguir las instrucciones de alta y las citas de seguimiento?",
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
    "q_post_pain": "Avez-vous une douleur intense ou croissante dans un œil ?",
    "q_post_vision": "Votre vision s’est-elle récemment dégradée ou se dégrade-t-elle après une amélioration ?",
    "q_post_redness": "Une rougeur, un gonflement ou des sécrétions collantes sont-ils apparus ou augmentent-ils ?",
    "q_post_flashes": "Avez-vous de nouveaux éclairs, une augmentation soudaine des corps flottants ou un voile comme un rideau ?",
    "q_post_glare": "Avez-vous actuellement des éblouissements ou une diffusion de la lumière ?",
    "q_post_worse": "L’éblouissement ou la gêne ne s’améliore-t-il pas avec le temps, ou s’aggrave-t-il ?",
    "q_post_followup": "Comprenez-vous et pouvez-vous suivre les consignes de sortie et le calendrier de suivi ?",
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
    "q_post_pain": "どちらかの目に強い痛み、または悪化する痛みがありますか？",
    "q_post_vision": "新たな視力低下や、一度改善した後に再び見えにくくなるなどの悪化がありますか？",
    "q_post_redness": "充血・腫れ・粘りのある目やにが新たに出た、または増えていますか？",
    "q_post_flashes": "光が走る、浮遊物が急に増える、カーテンのように視野が遮られる症状が新たにありますか？",
    "q_post_glare": "今、光のにじみやまぶしさがありますか？",
    "q_post_worse": "時間がたっても、まぶしさや不快感が改善しない、または悪化していますか？",
    "q_post_followup": "退院時の説明と次回の受診予定を理解し、そのとおりに対応できますか？",
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
    "q_post_pain": "任一眼是否有剧烈或逐渐加重的疼痛？",
    "q_post_vision": "是否新出现视力下降，或好转后再次变得模糊？",
    "q_post_redness": "是否新出现或加重的充血、肿胀或黏性分泌物？",
    "q_post_flashes": "是否新出现闪光、飞蚊突然增多或幕帘样视野遮挡？",
    "q_post_glare": "目前是否有眩光或光线散射？",
    "q_post_worse": "随着时间推移，眩光或不适是否没有改善，甚至加重？",
    "q_post_followup": "您是否理解并能遵循出院指导和复诊安排？",
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
/** 4주 초과 백내장·불명 수술 이력에서 '수술한 눈이 한쪽인가'를 물을 가치가 있는가.
 *  답이 판정을 바꿀 수 없으면(단안 클로즈업, 두 눈 판정 불일치) 묻지 않는다. */
function fellowEyeQuestionApplies() {
 return state.riskAnswers?.surgery === 'past'
  && ['cataract','unknown'].includes(state.riskAnswers?.surgery_type)
  && bothEyesAgree();
}
/** 수술하지 않은 반대쪽 눈의 판독을 그대로 쓸 수 있는가.
 *  'both'(양쪽 수술)·'unknown'(모르겠음)은 살릴 눈이 없거나 확신할 수 없으므로 제외한다.
 *  4주 이내(hasSurgery)는 술후 확인 경로 자체가 스크리닝이 아니므로 여기서 다루지 않는다. */
function fellowEyeAssessable() {
 return hasPhotoVerdict() && !hasSurgery()
  && state.riskAnswers?.surgery_both === 'one'
  && fellowEyeQuestionApplies();
}
// The upload has no reliable anatomical side. Do not apply its cataract score
// to a person with an artificial lens, or an unknown remote operation.
function photoAssessmentExcluded() {
 if (!hasPhotoVerdict()) return false;
 if (hasSurgery()) return true;
 const remoteLens = state.riskAnswers?.surgery === 'past'
  && ['cataract','unknown'].includes(state.riskAnswers.surgery_type);
 return remoteLens && !fellowEyeAssessable();
}
function effectiveCataractCode() {
 if (hasSurgery() || state.aiResultCode === 'postop') return 'postop';
 return photoAssessmentExcluded() ? 'excluded' : state.aiResultCode;
}
function startSymptomCheck() {
 resetScreeningState(); state.aiResultCode='skipped';
 showTab('tab-test'); nextStep('step-chat'); startChat();
}
const surgeryRiskQuestions = [
 ['surgery_type','surgery_type_q',['cataract','laser','other','unknown'],'surgery_type_'],
 ['surgery_eye','surgery_eye_q',['left','right','both'],'surgery_eye_'],
 ['surgery_sym_eye','surgery_sym_eye_q',['left','right','both','none'],'surgery_eye_']
].map(([code,key,values,prefix]) => ({code,key,type:'choice',options:values.map(v=>({v,key:prefix+v,score:0}))}));
// 4주 초과 이력 전용 문항. surgery_eye('가장 최근에 수술한 눈')를 재사용하면 안 된다 —
// 양안 백내장 수술은 몇 주 간격으로 따로 받는 것이 일반적이라, '가장 최근은 왼쪽'이라는
// 답을 '오른쪽은 수술하지 않았다'로 읽으면 인공수정체 눈을 판독해 버린다.
// 그래서 시기를 묻지 않고 '수술받은 눈이 한쪽인가 양쪽인가'만, 문항 안에서 명시해 묻는다.
const remoteSurgeryScopeQuestion = {
 code:'surgery_both', key:'surgery_both_q', type:'choice',
 options:['one','both','unknown'].map(v=>({v,key:'surgery_both_'+v,score:0}))
};
const postoperativeQuestions = ['pain','vision','redness','flashes','glare','worse','followup'].map(kind=>({
 code:'post_'+kind,key:'q_post_'+kind,disease:'general',weight:0,
 redFlag:['pain','vision','redness','flashes'].includes(kind),invert:kind==='followup',
 // 경과를 묻는 문항은 수술 당일에 물으면 안 된다. 좋아질 시간 자체가 없었기 때문에
 // 정상 회복 중인 사람도 '예'가 나오고, 당연한 술후 눈부심이 '병원에 문의하세요'로 올라간다.
 // (예전 q_post_change는 '수술 전에는 없었나'와 '좋아지지 않나'를 한 문장에 묶어서,
 //  당일 수술자는 앞 절이 항상 참이라 무조건 걸렸다.)
 ...(kind==='worse' ? {showIf:{code:'surgery',values:['recent']}} : {})
}));
function startPostoperativeCheck() {
 resetScreeningState();
 state.aiResultCode = 'postop';
 showTab('tab-test'); nextStep('step-chat'); startChat();
}
function postoperativeTriage(ctx, t) {
 const urgent=(ctx.redFlags || []).length>0;
 const a=state.symptomAnswers || {};
 // 사진 판독은 적용하지 않는다. 일반 검사에서 암슬러를 끝낸 뒤 수술 이력을
 // 답할 수도 있으므로, 이미 보고된 암슬러 이상은 유지한다.
 const contact=a.post_worse===true || a.post_followup===false || ctx.amslerAbnormal===true;
 const kind=urgent?'urgent':contact?'contact':'follow';
 return {level:urgent?'urgent':contact?'now':'monitor',label:t['post_'+kind],
  why:t['post_'+kind+'_why'],note:t.post_limit,riskScore:0,riskMax:13};
}
