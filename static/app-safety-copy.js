// Safety copy shared by the photo, questionnaire and report paths.
// Sources: https://www.nhs.uk/symptoms/floaters-and-flashes-in-the-eyes/
// https://www.nhs.uk/symptoms/eye-pain/
// https://www.guysandstthomas.nhs.uk/health-information/cataract-surgery/after-cataract-surgery
const safetyCopy = {
 ko: ['잘 보이지 않거나 검사할 수 없어요','미측정','이상 응답','이상 없음',
  '검사하지 못한 눈은 정상으로 판단할 수 없습니다. 새로 생기거나 악화된 시력 변화는 즉시 안과에 문의하세요.',
  '최근 처음으로 빛이 번쩍이거나, 날파리 같은 점이 갑자기 늘거나, 커튼 같은 그림자가 시야를 가리나요? (밤에 불빛이 번져 보이는 눈부심과는 다릅니다)',
  '새 번쩍임·비문증·커튼 같은 가림',
  '인공수정체 또는 종류가 불분명한 수술 이력이 있어 사진 판독을 적용하지 않습니다. 촬영한 눈과 수술한 눈의 일치 여부도 확인되지 않았습니다. 증상은 안과에서 확인하세요.',
  '사진 없이 증상 확인하기','수술한 눈·안대·촬영 어려움 → 문진',
  '갑작스러운 시력저하, 심한 눈 통증, 새 번쩍임·비문증·커튼 같은 가림은 앱 검사를 기다리지 말고 즉시 안과에 문의하세요.',
  '눈동자가 또렷하게 보여요 · 분석하기',
  '검사할 눈의 홍채와 동공이 또렷하게 보여야 합니다. 감은 눈·안경 반사·컬러렌즈·흐린 사진은 다시 골라주세요. 수술한 눈이나 의료용 안대·보호대가 있다면 문진을 선택하세요. 촬영을 위해 보호대를 임의로 벗기지 마세요. 자동 검사는 가려진 눈을 놓칠 수 있습니다.'],
 en: ['I cannot see clearly or do this test','Not tested','Abnormal','No change',
  'An untested eye cannot be called normal. Contact eye care urgently for new or worsening vision changes.',
  'Have flashes appeared for the first time, have floaters suddenly increased, or is a curtain-like shadow covering your vision? (This is not the same as lights glaring or streaking at night.)',
  'New flashes / floaters / curtain',
  'Photo interpretation is excluded because of an artificial lens or an unspecified eye operation. The photographed and operated eye cannot be reliably matched. Have symptoms checked by eye care.',
  'Check symptoms without a photo','Operated eye / eye patch / no photo → questions',
  'Sudden vision loss, severe eye pain, new flashes, floaters or a curtain-like shadow: contact urgent eye care without waiting for this app.',
  'Iris and pupil are clear · Analyze',
  'The tested iris and pupil must be clear. Retake closed-eye, reflective, coloured-contact or blurred photos. For an operated eye or medical patch/shield, choose questions. Do not remove medical protection just for this photo. Automatic checks can miss obscured eyes.'],
 es: ['No veo bien o no puedo hacer la prueba','Sin evaluar','Alterado','Sin cambios',
  'Un ojo sin evaluar no puede considerarse normal. Consulte urgentemente por cambios visuales nuevos o que empeoran.',
  '¿Ve destellos por primera vez, han aumentado de repente las moscas volantes o una sombra como cortina tapa la visión? (No es lo mismo que el deslumbramiento de las luces por la noche.)',
  'Destellos / moscas nuevas / cortina',
  'No se interpreta la foto por una lente artificial o cirugía no especificada. No se puede vincular con certeza el ojo fotografiado y operado. Consulte los síntomas con un oftalmólogo.',
  'Consultar síntomas sin foto','Ojo operado / parche / sin foto → preguntas',
  'Pérdida súbita de visión, dolor intenso, destellos, nuevas moscas volantes o cortina: consulte urgentemente sin esperar a la app.',
  'El iris y la pupila se ven con claridad · Analizar',
  'El iris y la pupila deben verse claramente. Repita fotos borrosas, con reflejos, ojos cerrados o lentes de color. Para ojos operados o con protector médico, elija preguntas. No retire el protector para la foto. El control automático puede fallar.'],
 fr: ['Je vois mal ou ne peux pas faire ce test','Non testé','Anormal','Sans changement',
  'Un œil non testé ne peut pas être déclaré normal. Consultez en urgence pour une vision qui change ou se dégrade.',
  'Voyez-vous de nouveaux éclairs, une hausse soudaine de corps flottants ou une ombre comme un rideau dans votre vision ? (Ce n’est pas l’éblouissement des lumières la nuit.)',
  'Nouveaux éclairs / corps flottants / rideau',
  'Photo non interprétée : cristallin artificiel ou opération non précisée. Le lien entre œil photographié et opéré est incertain. Faites examiner vos symptômes.',
  'Vérifier les symptômes sans photo','Œil opéré / protection / sans photo → questions',
  'Perte soudaine de vision, douleur intense, nouveaux éclairs, corps flottants ou rideau : consultez en urgence sans attendre cette application.',
  'Iris et pupille sont nets · Analyser',
  'Iris et pupille doivent être nets. Reprenez les photos floues, avec reflets, yeux fermés ou lentilles colorées. Pour un œil opéré ou protégé, choisissez les questions. Ne retirez pas une protection médicale pour la photo. Le contrôle automatique peut échouer.'],
 ja: ['よく見えない・検査できない','未測定','異常あり','異常なし',
  '検査できなかった目を正常とは判断できません。新しい、または悪化する見え方の変化は直ちに眼科へ相談してください。',
  '初めて光が走る、飛蚊症が急に増える、カーテンのような影が視野を遮ることがありますか？（夜に光がにじんで見えるまぶしさとは異なります）',
  '新しい光視症・飛蚊症・カーテン状の影',
  '人工水晶体または種類不明の手術歴があるため写真判読は適用しません。撮影した目と手術した目の一致も未確認です。症状は眼科で確認してください。',
  '写真なしで症状を確認','手術した目・眼帯・撮影困難 → 問診',
  '急な視力低下、強い眼痛、新しい光視症・飛蚊症・カーテン状の影は、アプリを待たず直ちに眼科へ相談してください。',
  '虹彩と瞳孔がはっきり見えます・分析する',
  '虹彩と瞳孔が明瞭な写真を選んでください。閉じた目、反射、カラーコンタクト、ぼやけた写真は撮り直してください。手術した目や医療用眼帯・保護具がある場合は問診へ。撮影のために保護具を勝手に外さないでください。自動確認は遮られた目を見逃すことがあります。'],
 zh: ['看不清或无法完成检查','未测量','异常','无异常',
  '无法检查的眼睛不能视为正常。出现新的或加重的视力变化，请立即咨询眼科。',
  '是否首次出现闪光、飞蚊突然增多，或幕帘样阴影遮挡视野？（与夜间灯光发散的眩光不同）',
  '新闪光／飞蚊／幕帘样遮挡',
  '因存在人工晶状体或类型不明的手术史，不采用照片判读。也无法可靠确认拍摄眼与手术眼是否一致。请到眼科检查症状。',
  '不上传照片，检查症状','手术眼／眼罩／无法拍摄 → 问卷',
  '突然视力下降、剧烈眼痛、新闪光、飞蚊或幕帘样遮挡：不要等待应用检查，请立即咨询眼科。',
  '虹膜和瞳孔清晰可见 · 开始分析',
  '请确认虹膜和瞳孔清晰可见。闭眼、反光、彩色隐形眼镜或模糊照片请重新选择。手术眼或佩戴医用眼罩、防护罩时请选择问卷。不要为拍照自行摘除医疗防护。自动检查可能漏掉被遮挡的眼睛。']
};
for(const [lang,values] of Object.entries(safetyCopy)) {
 const keys=['ams_unable','ams_unmeasured','ams_eye_bad','ams_eye_ok','ams_unable_note','q_rf_flashes','sym_rf_flashes','photo_history_limit','symptom_entry','photo_symptom_entry','early_warning','review_confirm','review_body'];
 keys.forEach((key,i)=>translations[lang][key]=values[i]);
}
// 사진을 한 장도 받지 않은 회차('사진 없이 증상 확인' 입구, 수술 후 입구에서 4주 초과로
// 답한 경우)를 위한 문구. 이게 없던 동안 리포트 '1. 백내장 AI 결과'에 값이 "-" 하나만
// 찍혔고, 고령 사용자가 그것을 '이상 없음'으로 읽을 수 있었다.
const noPhotoCopy = {
 ko:['사진 분석을 하지 않은 회차입니다. 이 리포트에는 백내장 사진 판독 결과가 없습니다.','1. 사진 판독 (이번 검사에는 적용하지 않음)'],
 en:['No photo was analysed in this session. This report contains no cataract photo result.','1. Photo analysis (not applied in this session)'],
 es:['En esta sesión no se analizó ninguna foto. Este informe no incluye un resultado fotográfico de catarata.','1. Análisis de la foto (no aplicado en esta sesión)'],
 fr:['Aucune photo n’a été analysée cette fois. Ce rapport ne contient aucun résultat photo de cataracte.','1. Analyse de la photo (non appliquée cette fois)'],
 ja:['今回は写真分析を行っていません。このレポートに白内障の写真判読結果はありません。','1. 写真判読（今回は適用しません）'],
 zh:['本次未进行照片分析。本报告不包含白内障照片判读结果。','1. 照片判读（本次不适用）']
};
for(const [lang,[skipped,label]] of Object.entries(noPhotoCopy)) Object.assign(translations[lang],{photo_skipped:skipped,rep_l1_excluded:label});
// 한쪽 눈만 수술한 사람의 반대쪽 눈 판독.
// 문항은 '가장 최근'이 아니라 '지금까지 받은 모든 수술'을 묻는다 — 양안 백내장 수술은
// 몇 주 간격으로 따로 받는 것이 일반적이라, 시기를 섞으면 인공수정체 눈을 판독해 버린다.
const fellowEyeCopy = {
 ko:['지금까지 눈 수술을 받은 눈은 한쪽인가요, 양쪽인가요? (시기가 다르더라도 받은 적이 있으면 모두 포함해 주세요)',
  '한쪽 눈만 받았어요','양쪽 눈 모두 받았어요','잘 모르겠어요','수술하지 않은 눈 기준',
  '수술한 눈은 인공수정체가 있어 판독에서 제외했습니다. 아래 백내장 판독은 수술하지 않은 눈에 대한 것입니다.'],
 en:['Have you had eye surgery on one eye or on both? Include every operation, even if they happened at different times.',
  'One eye only','Both eyes','Not sure','Unoperated eye only',
  'The operated eye was excluded because of its artificial lens. The cataract reading below refers to the unoperated eye.'],
 es:['¿Le han operado de un ojo o de los dos? Incluya todas las cirugías, aunque fueran en momentos distintos.',
  'Solo un ojo','Ambos ojos','No estoy seguro/a','Solo el ojo no operado',
  'El ojo operado se excluyó por su lente artificial. La lectura de catarata siguiente corresponde al ojo no operado.'],
 fr:['Avez-vous été opéré d’un seul œil ou des deux ? Comptez toutes les opérations, même à des dates différentes.',
  'D’un seul œil','Des deux yeux','Je ne sais pas','Œil non opéré uniquement',
  'L’œil opéré a été exclu en raison de son implant. La lecture de cataracte ci-dessous concerne l’œil non opéré.'],
 ja:['これまでに手術を受けた目は片方だけですか、両方ですか？時期が違っても、受けたものはすべて含めてください。',
  '片方の目だけ','両方の目','わかりません','手術していない目のみ',
  '手術した目は眼内レンズがあるため判読から除外しました。以下の白内障判読は手術していない目に対するものです。'],
 zh:['您做过手术的眼睛是一只还是两只？即使时间不同，也请把所有手术都算进来。',
  '只有一只眼','两只眼','不清楚','仅未手术眼',
  '手术眼因植入人工晶状体已排除判读。以下白内障判读针对未手术眼。']
};
for(const [lang,v] of Object.entries(fellowEyeCopy)) Object.assign(translations[lang],
 {surgery_both_q:v[0],surgery_both_one:v[1],surgery_both_both:v[2],surgery_both_unknown:v[3],
  photo_fellow_only:v[4],find_cat_fellow:v[5]});
// 사진에서 나온 좌/우는 해부학적 좌우가 아니다.
//
// vision.py는 eyes[].side를 ["left","right"]로 붙이는데, eye_detector.py가 사진의
// x좌표로 정렬한 결과다("사진 기준"). 셀카는 기기·앱 설정에 따라 거울상으로 저장되므로
// 사진 왼쪽에 보이는 눈이 실제 왼눈인지 알 수 없다. 그런데 화면 라벨은 암슬러와 같은
// eye_left("왼쪽 눈")를 함께 쓰고 있었다 — 암슬러는 사용자가 직접 한쪽을 가렸으니
// 해부학적으로 맞지만, 사진은 아니다. 두 뜻이 같은 단어를 쓰면 사용자가 사진 결과의
// 좌우를 자기 눈으로 그대로 읽는다. 그래서 사진 전용 라벨을 따로 둔다.
// (암슬러·수술 문항의 eye_left/eye_right는 그대로 둔다.)
const photoSideCopy = {
 ko:['사진 왼쪽 눈','사진 오른쪽 눈',
  '※ 좌·우는 사진에 보이는 위치 기준입니다. 셀카는 좌우가 뒤집혀 저장될 수 있어 실제 눈과 다를 수 있습니다. 얼굴 사진의 눈별 수치는 참고용이며, 정확도는 눈 클로즈업 촬영이 더 높습니다.'],
 en:['Left in photo','Right in photo',
  '※ Left and right refer to positions in the photo. Selfies can be saved mirrored, so these may not match your actual eyes. Per-eye values from a face photo are for reference; a close-up of the eye is more accurate.'],
 es:['Izquierdo en la foto','Derecho en la foto',
  '※ Izquierda y derecha se refieren a la posición en la foto. Los selfies pueden guardarse en espejo, así que puede no coincidir con sus ojos reales. Los valores por ojo de una foto del rostro son orientativos; un primer plano es más preciso.'],
 fr:['Gauche sur la photo','Droite sur la photo',
  '※ Gauche et droite désignent la position sur la photo. Les selfies peuvent être enregistrés en miroir : cela peut ne pas correspondre à vos yeux réels. Les valeurs par œil issues d’une photo du visage sont indicatives ; un gros plan est plus précis.'],
 ja:['写真の左の目','写真の右の目',
  '※ 左右は写真に写っている位置の基準です。セルフィーは左右反転で保存されることがあり、実際の目と異なる場合があります。顔写真の目ごとの数値は参考用で、目のクローズアップ撮影の方が精度が高いです。'],
 zh:['照片中左侧眼','照片中右侧眼',
  '※ 左右指照片中的位置。自拍可能以镜像保存，因此可能与您实际的眼睛不一致。面部照片的逐眼数值仅供参考，眼部特写拍摄的准确度更高。']
};
for(const [lang,[l,r,note]] of Object.entries(photoSideCopy)) Object.assign(translations[lang],
 {eye_photo_left:l,eye_photo_right:r,eye_ref_note:note});
const painCopy = {
 ko:['지금 어느 쪽 눈이든 심한 통증이 있나요? 두통·구역질·무지개 테가 없어도 답해주세요.','심한 눈 통증'],
 en:['Do you have severe pain in either eye now, even without headache, nausea or halos?','Severe eye pain'],
 es:['¿Tiene dolor intenso en algún ojo, incluso sin dolor de cabeza, náuseas ni halos?','Dolor ocular intenso'],
 fr:['Avez-vous une forte douleur dans un œil, même sans maux de tête, nausées ni halos ?','Forte douleur oculaire'],
 ja:['今、どちらかの目に強い痛みがありますか？頭痛・吐き気・虹輪視がなくてもお答えください。','強い眼痛'],
 zh:['现在任一眼是否剧烈疼痛？即使没有头痛、恶心或虹视也请回答。','剧烈眼痛']
};
for(const [lang,[question,label]] of Object.entries(painCopy)) Object.assign(translations[lang],{q_rf_pain:question,sym_rf_pain:label});
