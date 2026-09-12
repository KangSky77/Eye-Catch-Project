// Safety copy shared by the photo, questionnaire and report paths.
// Sources: https://www.nhs.uk/symptoms/floaters-and-flashes-in-the-eyes/
// https://www.nhs.uk/symptoms/eye-pain/
// https://www.guysandstthomas.nhs.uk/health-information/cataract-surgery/after-cataract-surgery
const safetyCopy = {
 ko: ['잘 보이지 않거나 검사할 수 없어요','미측정','이상 응답','이상 없음',
  '검사하지 못한 눈은 정상으로 판단할 수 없습니다. 새로 생기거나 악화된 시력 변화는 즉시 안과에 문의하세요.',
  '최근 처음으로 빛이 번쩍이거나, 날파리 같은 점이 갑자기 늘거나, 커튼 같은 그림자가 시야를 가리나요?',
  '새 번쩍임·비문증·커튼 같은 가림',
  '인공수정체 또는 종류가 불분명한 수술 이력이 있어 사진 판독을 적용하지 않습니다. 촬영한 눈과 수술한 눈의 일치 여부도 확인되지 않았습니다. 증상은 안과에서 확인하세요.',
  '사진 없이 증상 확인하기','수술한 눈·안대·촬영 어려움 → 문진',
  '갑작스러운 시력저하, 심한 눈 통증, 새 번쩍임·비문증·커튼 같은 가림은 앱 검사를 기다리지 말고 즉시 안과에 문의하세요.',
  '수술하지 않은 눈동자가 보여요 · 분석하기',
  '검사할 눈의 홍채와 동공이 또렷하게 보여야 합니다. 감은 눈·안경 반사·컬러렌즈·흐린 사진은 다시 골라주세요. 수술한 눈이나 의료용 안대·보호대가 있다면 문진을 선택하세요. 촬영을 위해 보호대를 임의로 벗기지 마세요. 자동 검사는 가려진 눈을 놓칠 수 있습니다.'],
 en: ['I cannot see clearly or do this test','Not tested','Abnormal','No change',
  'An untested eye cannot be called normal. Contact eye care urgently for new or worsening vision changes.',
  'Have flashes appeared for the first time, have floaters suddenly increased, or is a curtain-like shadow covering your vision?',
  'New flashes / floaters / curtain',
  'Photo interpretation is excluded because of an artificial lens or an unspecified eye operation. The photographed and operated eye cannot be reliably matched. Have symptoms checked by eye care.',
  'Check symptoms without a photo','Operated eye / eye patch / no photo → questions',
  'Sudden vision loss, severe eye pain, new flashes, floaters or a curtain-like shadow: contact urgent eye care without waiting for this app.',
  'Unoperated iris and pupil visible · Analyze',
  'The tested iris and pupil must be clear. Retake closed-eye, reflective, coloured-contact or blurred photos. For an operated eye or medical patch/shield, choose questions. Do not remove medical protection just for this photo. Automatic checks can miss obscured eyes.'],
 es: ['No veo bien o no puedo hacer la prueba','Sin evaluar','Alterado','Sin cambios',
  'Un ojo sin evaluar no puede considerarse normal. Consulte urgentemente por cambios visuales nuevos o que empeoran.',
  '¿Ve destellos por primera vez, han aumentado de repente las moscas volantes o una sombra como cortina tapa la visión?',
  'Destellos / moscas nuevas / cortina',
  'No se interpreta la foto por una lente artificial o cirugía no especificada. No se puede vincular con certeza el ojo fotografiado y operado. Consulte los síntomas con un oftalmólogo.',
  'Consultar síntomas sin foto','Ojo operado / parche / sin foto → preguntas',
  'Pérdida súbita de visión, dolor intenso, destellos, nuevas moscas volantes o cortina: consulte urgentemente sin esperar a la app.',
  'Iris y pupila no operados visibles · Analizar',
  'El iris y la pupila deben verse claramente. Repita fotos borrosas, con reflejos, ojos cerrados o lentes de color. Para ojos operados o con protector médico, elija preguntas. No retire el protector para la foto. El control automático puede fallar.'],
 fr: ['Je vois mal ou ne peux pas faire ce test','Non testé','Anormal','Sans changement',
  'Un œil non testé ne peut pas être déclaré normal. Consultez en urgence pour une vision qui change ou se dégrade.',
  'Voyez-vous de nouveaux éclairs, une hausse soudaine de corps flottants ou une ombre comme un rideau dans votre vision ?',
  'Nouveaux éclairs / corps flottants / rideau',
  'Photo non interprétée : cristallin artificiel ou opération non précisée. Le lien entre œil photographié et opéré est incertain. Faites examiner vos symptômes.',
  'Vérifier les symptômes sans photo','Œil opéré / protection / sans photo → questions',
  'Perte soudaine de vision, douleur intense, nouveaux éclairs, corps flottants ou rideau : consultez en urgence sans attendre cette application.',
  'Iris et pupille non opérés visibles · Analyser',
  'Iris et pupille doivent être nets. Reprenez les photos floues, avec reflets, yeux fermés ou lentilles colorées. Pour un œil opéré ou protégé, choisissez les questions. Ne retirez pas une protection médicale pour la photo. Le contrôle automatique peut échouer.'],
 ja: ['よく見えない・検査できない','未測定','異常あり','異常なし',
  '検査できなかった目を正常とは判断できません。新しい、または悪化する見え方の変化は直ちに眼科へ相談してください。',
  '初めて光が走る、飛蚊症が急に増える、カーテンのような影が視野を遮ることがありますか？',
  '新しい光視症・飛蚊症・カーテン状の影',
  '人工水晶体または種類不明の手術歴があるため写真判読は適用しません。撮影した目と手術した目の一致も未確認です。症状は眼科で確認してください。',
  '写真なしで症状を確認','手術した目・眼帯・撮影困難 → 問診',
  '急な視力低下、強い眼痛、新しい光視症・飛蚊症・カーテン状の影は、アプリを待たず直ちに眼科へ相談してください。',
  '未手術の虹彩と瞳孔が見える・分析',
  '虹彩と瞳孔が明瞭な写真を選んでください。閉じた目、反射、カラーコンタクト、ぼやけた写真は撮り直してください。手術した目や医療用眼帯・保護具がある場合は問診へ。撮影のために保護具を勝手に外さないでください。自動確認は遮られた目を見逃すことがあります。'],
 zh: ['看不清或无法完成检查','未测量','异常','无异常',
  '无法检查的眼睛不能视为正常。出现新的或加重的视力变化，请立即咨询眼科。',
  '是否首次出现闪光、飞蚊突然增多，或幕帘样阴影遮挡视野？',
  '新闪光／飞蚊／幕帘样遮挡',
  '因存在人工晶状体或类型不明的手术史，不采用照片判读。也无法可靠确认拍摄眼与手术眼是否一致。请到眼科检查症状。',
  '不上传照片，检查症状','手术眼／眼罩／无法拍摄 → 问卷',
  '突然视力下降、剧烈眼痛、新闪光、飞蚊或幕帘样遮挡：不要等待应用检查，请立即咨询眼科。',
  '未手术的虹膜和瞳孔清晰 · 分析',
  '请确认虹膜和瞳孔清晰可见。闭眼、反光、彩色隐形眼镜或模糊照片请重新选择。手术眼或佩戴医用眼罩、防护罩时请选择问卷。不要为拍照自行摘除医疗防护。自动检查可能漏掉被遮挡的眼睛。']
};
for(const [lang,values] of Object.entries(safetyCopy)) {
 const keys=['ams_unable','ams_unmeasured','ams_eye_bad','ams_eye_ok','ams_unable_note','q_rf_flashes','sym_rf_flashes','photo_history_limit','symptom_entry','photo_symptom_entry','early_warning','review_confirm','review_body'];
 keys.forEach((key,i)=>translations[lang][key]=values[i]);
}
const painCopy = {
 ko:['지금 어느 쪽 눈이든 심한 통증이 있나요? 두통·구역질·무지개 테가 없어도 답해주세요.','심한 눈 통증'],
 en:['Do you have severe pain in either eye now, even without headache, nausea or halos?','Severe eye pain'],
 es:['¿Tiene dolor intenso en algún ojo, incluso sin dolor de cabeza, náuseas ni halos?','Dolor ocular intenso'],
 fr:['Avez-vous une forte douleur dans un œil, même sans maux de tête, nausées ni halos ?','Forte douleur oculaire'],
 ja:['今、どちらかの目に強い痛みがありますか？頭痛・吐き気・虹輪視がなくてもお答えください。','強い眼痛'],
 zh:['现在任一眼是否剧烈疼痛？即使没有头痛、恶心或虹视也请回答。','剧烈眼痛']
};
for(const [lang,[question,label]] of Object.entries(painCopy)) Object.assign(translations[lang],{q_rf_pain:question,sym_rf_pain:label});
