const translations = {
    ko: {
        nav_test: "AI 검사", nav_disease: "질환 소개", nav_report: "진단 리포트", nav_map: "병원 찾기",
        intro_title: "당신의 눈 건강,<br>AI가 지켜드립니다", intro_desc: "안구 사진 자동 분석과 전문 문진을 통해 주요 안질환 위험도를 체크합니다.",
        start_btn: "분석 시작하기", upload_title: "사진 업로드", upload_btn: "사진 선택 및 전송",
        guide_title: "⚠️ 정확한 분석 가이드", guide_list: "<li>정면에서 촬영하세요.</li><li>빛 반사에 주의하세요.</li>",
        tips_title: "정확한 분석을 위한<br>촬영 꿀팁", tip1_t: "전면보다는 후면 카메라!", tip1_d: "후면 카메라가 화질이 좋고 빛 반사가 적어요.", tip2_t: "플래시를 켜주세요", tip2_d: "어두운 곳보다는 밝은 곳에서 플래시를 쓰면 더 정확해요.", tip3_t: "30cm 거리를 유지하세요", tip3_d: "너무 가까우면 초점이 흐려질 수 있어요.", tips_btn: "이해했습니다!",
        loading_title: "AI 딥러닝 분석 중...", ai_res_title: "백내장 판별 결과", next_amsler: "2단계: 황반변성 테스트",
        ams_title: "황반변성 자가진단", ams_ok: "정상 (곧게 보임)", ams_bad: "휘어보임/암점",
        chat_yes: "네", chat_no: "아니오", dis_main_title: "4대 주요 안질환 안내", rep_title: "Eye-Catch 진단 리포트",
        rep_l1: "1. 백내장 AI 결과", rep_l2: "2. 황반변성 결과", rep_l3: "3. 문진 소견", rep_l4: "4. Gemma AI 맞춤 소견 ✨", pdf_btn: "📄 PDF 다운로드", map_btn: "🏥 내 주변 안과 찾기 (Kakao)",
        msg_gen: "리포트를 생성 중입니다...", res_ams_bad: "이상 소견 (검사 요망)", res_ams_ok: "특이사항 없음", res_chat_none: "주요 증상 없음",
        rep_warn: "본 리포트는 AI 자가진단 보조 자료입니다. 정확한 진단을 위해 안과 전문의와 상담하시기 바랍니다.",
        dis_card_hint: "카드를 누르면 자세한 설명을 확인할 수 있어요.", dis_more: "자세히 보기 →", dis_modal_note: "이런 증상이 의심되면 안과 검진을 받아보세요.", dm_close: "닫기", dis_ai_badge: "AI 분석 지원",
        map_page_title: "내 주변 안과 찾기", map_locate: "📍 내 위치로 찾기", map_open_full: "카카오맵에서 전체 보기",
        map_status_idle: "아래 버튼을 눌러 가까운 안과를 찾아보세요.", map_status_loading: "위치를 확인하는 중...", map_status_denied: "위치 권한이 거부되었어요. 전체 지도에서 검색해 주세요.", map_status_unsupported: "이 브라우저는 위치 기능을 지원하지 않아요.",
        map_you: "📍 내 위치", map_searching: "주변 안과를 찾는 중... ⏳", map_found: "주변 안과 {n}곳을 찾았어요.", map_none: "주변에서 안과를 찾지 못했어요. 전체 지도에서 검색해 주세요.", map_search_err: "안과 검색에 실패했어요. 전체 지도에서 검색해 주세요.", map_directions: "길찾기",
        ai_normal: "특이 소견 없음 (정상)", ai_risk: "백내장 위험 단계 (정밀 검사 권장)", ai_borderline: "경계 단계 (재촬영 후 재검사 또는 안과 검진 권장)", ai_invalid: "눈 사진이 아닌 것 같아요. 눈을 가까이서 촬영한 사진을 올려주세요.",
        face_mode_note: "👁 얼굴 사진에서 눈 {n}곳을 찾아 분석했어요.",
        eye_breakdown_title: "눈별 분석 (사진 기준)", eye_left: "왼쪽 눈", eye_right: "오른쪽 눈", eye_unilateral: "⚠️ 편측 의심 — 한쪽 눈만 위험 신호", eye_ref_note: "※ 얼굴 사진의 눈별 수치는 참고용이며, 정확도는 눈 클로즈업 촬영이 더 높습니다.",
        loading_elapsed: "{s}초 경과",
        gemma_idle: "먼저 'AI 검사'를 진행하면 맞춤 소견이 여기에 표시됩니다.", rep_followup_title: "🤖 AI에게 더 궁금한 점 물어보기", rep_followup_ph: "예: 관리 방법 알려줘",
        srv_err: "⚠️ 서버와 연결할 수 없습니다.", nextq_fallback: "추가적으로 눈이 불편하신 곳이 있나요?",
        survey_done: "기본 문진이 완료되었습니다. 맞춤형 추가 질문을 생성 중입니다... ⏳", next_q_generating: "다음 맞춤형 질문을 생성 중입니다... ⏳", symptom_extra: "기타 의심 증상 추가 발견",
        opinion_writing: "AI가 소견서를 작성 중입니다... ✍️\n\n", opinion_error: "⚠️ 로컬 AI 서버와 연결이 끊어졌습니다.",
        notif_title: "Eye-Catch 진단 완료 🏥", notif_body: "AI 맞춤형 소견서 작성이 완료되었습니다! 결과를 확인해보세요.", followup_thinking: "답변을 생각하고 있습니다... 🤔\n\n",
        pdf_doc_title: "Eye-Catch 정밀 진단 리포트", pdf_issued: "발급일자", pdf_s1: "1. 백내장 AI 분석 결과", pdf_s2: "2. 황반변성 자가진단 (Amsler Grid)", pdf_s3: "3. AI 문진 주요 소견", pdf_s4: "4. 종합 AI 소견서 (Powered by Gemma)",
        pdf_footer: "본 리포트는 인공지능 기반의 자가진단 보조 자료입니다.<br>정확한 진단 및 처방을 위해서는 반드시 안과 전문의와 상담하시기 바랍니다."
    },
    en: {
        nav_test: "AI Analysis", nav_disease: "Diseases", nav_report: "Report", nav_map: "Find Clinic",
        intro_title: "Your Eye Health,<br>Protected by AI", intro_desc: "AI photo analysis and survey to check major eye disease risks.",
        start_btn: "Start Analysis", upload_title: "Upload Photo", upload_btn: "Select & Send",
        guide_title: "⚠️ Analysis Guide", guide_list: "<li>Face front.</li><li>Avoid glare/reflections.</li>",
        tips_title: "Photo Tips for<br>Accurate Analysis", tip1_t: "Use the rear camera!", tip1_d: "The rear camera has better quality and less glare.", tip2_t: "Turn on the flash", tip2_d: "Using flash in a bright place gives more accurate results.", tip3_t: "Keep about 30cm distance", tip3_d: "Too close and the photo may be out of focus.", tips_btn: "Got it!",
        loading_title: "AI Analyzing...", ai_res_title: "Cataract Result", next_amsler: "Step 2: Macular Test",
        ams_title: "Amsler Grid Test", ams_ok: "Normal (Straight)", ams_bad: "Distorted/Spot",
        chat_yes: "Yes", chat_no: "No", dis_main_title: "Major Eye Diseases", rep_title: "Eye-Catch Diagnostic Report",
        rep_l1: "1. Cataract AI", rep_l2: "2. Macular Test", rep_l3: "3. Survey Result", rep_l4: "4. Gemma AI Personalized Opinion ✨", pdf_btn: "📄 Download PDF", map_btn: "🌎 Find Clinic (Google)",
        msg_gen: "Generating report...", res_ams_bad: "Distortion detected", res_ams_ok: "Normal", res_chat_none: "No symptoms",
        rep_warn: "This is an AI-assisted tool. Please consult an ophthalmologist for an accurate diagnosis.",
        dis_card_hint: "Tap a card to see the full description.", dis_more: "Learn more →", dis_modal_note: "If you notice these symptoms, please see an ophthalmologist.", dm_close: "Close", dis_ai_badge: "AI-Powered",
        map_page_title: "Find a Clinic Near You", map_locate: "📍 Use My Location", map_open_full: "Open Full Map",
        map_status_idle: "Tap the button below to find nearby eye clinics.", map_status_loading: "Locating you...", map_status_denied: "Location denied. Please search on the full map.", map_status_unsupported: "This browser does not support geolocation.",
        map_you: "📍 You are here", map_searching: "Searching nearby eye clinics... ⏳", map_found: "Found {n} eye clinic(s) nearby.", map_none: "No eye clinics found nearby. Please search on the full map.", map_search_err: "Search failed. Please use the full map.", map_directions: "Directions",
        ai_normal: "No significant findings (Normal)", ai_risk: "Cataract risk stage (Detailed exam recommended)", ai_borderline: "Borderline (Retake the photo or consider an eye exam)", ai_invalid: "This doesn't look like an eye photo. Please upload a close-up of your eye.",
        face_mode_note: "👁 Detected {n} eye(s) in the face photo and analyzed them.",
        eye_breakdown_title: "Per-eye analysis (as in photo)", eye_left: "Left eye", eye_right: "Right eye", eye_unilateral: "⚠️ Possible one-sided (unilateral) — only one eye flagged", eye_ref_note: "※ Per-eye values from a face photo are for reference; a close-up of the eye is more accurate.",
        loading_elapsed: "{s}s elapsed",
        gemma_idle: "Complete the AI analysis first to see your personalized opinion here.", rep_followup_title: "🤖 Ask the AI more questions", rep_followup_ph: "e.g. How should I care for my eyes?",
        srv_err: "⚠️ Unable to connect to the server.", nextq_fallback: "Is there anything else bothering your eyes?",
        survey_done: "Basic survey complete. Generating a personalized follow-up question... ⏳", next_q_generating: "Generating the next personalized question... ⏳", symptom_extra: "Additional suspected symptom found",
        opinion_writing: "The AI is writing your opinion... ✍️\n\n", opinion_error: "⚠️ Connection to the local AI server was lost.",
        notif_title: "Eye-Catch Diagnosis Complete 🏥", notif_body: "Your personalized AI opinion is ready! Check your results.", followup_thinking: "Thinking of an answer... 🤔\n\n",
        pdf_doc_title: "Eye-Catch Diagnostic Report", pdf_issued: "Issued", pdf_s1: "1. Cataract AI Analysis", pdf_s2: "2. Macular Self-Test (Amsler Grid)", pdf_s3: "3. AI Survey Findings", pdf_s4: "4. Comprehensive AI Opinion (Powered by Gemma)",
        pdf_footer: "This report is an AI-assisted self-screening aid.<br>Please consult an ophthalmologist for an accurate diagnosis and treatment."
    },
    es: {
        nav_test: "Análisis IA", nav_disease: "Enfermedades", nav_report: "Informe", nav_map: "Clínicas",
        intro_title: "Tu salud ocular,<br>protegida por IA", intro_desc: "Análisis de fotos y encuesta para detectar riesgos oculares.",
        start_btn: "Iniciar análisis", upload_title: "Subir foto", upload_btn: "Seleccionar foto",
        guide_title: "⚠️ Guía", guide_list: "<li>Mira al frente.</li><li>Evita reflejos.</li>",
        tips_title: "Consejos de foto para<br>un análisis preciso", tip1_t: "¡Use la cámara trasera!", tip1_d: "La cámara trasera tiene mejor calidad y menos reflejos.", tip2_t: "Encienda el flash", tip2_d: "Usar el flash en un lugar luminoso da resultados más precisos.", tip3_t: "Mantenga unos 30 cm de distancia", tip3_d: "Si está muy cerca, la foto puede salir desenfocada.", tips_btn: "¡Entendido!",
        loading_title: "IA analizando...", ai_res_title: "Resultado de Cataratas", next_amsler: "Paso 2: Mácula",
        ams_title: "Prueba de Amsler", ams_ok: "Normal (Recto)", ams_bad: "Distorsionado/Mancha",
        chat_yes: "Sí", chat_no: "No", dis_main_title: "Enfermedades Oculares", rep_title: "Informe Diagnóstico Eye-Catch",
        rep_l1: "1. IA de Cataratas", rep_l2: "2. Prueba Macular", rep_l3: "3. Encuesta", rep_l4: "4. Opinión de Gemma AI ✨", pdf_btn: "📄 Descargar PDF", map_btn: "🌎 Buscar Clínica (Google)",
        msg_gen: "Generando informe...", res_ams_bad: "Distorsión", res_ams_ok: "Normal", res_chat_none: "Sin síntomas",
        rep_warn: "Herramienta asistida por IA. Consulte a un oftalmólogo para un diagnóstico preciso.",
        dis_card_hint: "Toca una tarjeta para ver la descripción completa.", dis_more: "Ver más →", dis_modal_note: "Si nota estos síntomas, consulte a un oftalmólogo.", dm_close: "Cerrar", dis_ai_badge: "Análisis con IA",
        map_page_title: "Encontrar una clínica cercana", map_locate: "📍 Usar mi ubicación", map_open_full: "Abrir mapa completo",
        map_status_idle: "Pulse el botón para encontrar clínicas cercanas.", map_status_loading: "Localizando...", map_status_denied: "Ubicación denegada. Busque en el mapa completo.", map_status_unsupported: "Este navegador no admite geolocalización.",
        map_you: "📍 Estás aquí", map_searching: "Buscando clínicas cercanas... ⏳", map_found: "{n} clínica(s) oftalmológica(s) cerca.", map_none: "No se encontraron clínicas cerca. Busque en el mapa completo.", map_search_err: "Búsqueda fallida. Use el mapa completo.", map_directions: "Cómo llegar",
        ai_normal: "Sin hallazgos significativos (Normal)", ai_risk: "Riesgo de cataratas (Se recomienda examen detallado)", ai_borderline: "Resultado límite (Repita la foto o considere un examen ocular)", ai_invalid: "Esto no parece una foto de un ojo. Suba un primer plano de su ojo.",
        face_mode_note: "👁 Se detectaron {n} ojo(s) en la foto del rostro y se analizaron.",
        eye_breakdown_title: "Análisis por ojo (según la foto)", eye_left: "Ojo izquierdo", eye_right: "Ojo derecho", eye_unilateral: "⚠️ Posible unilateral — solo un ojo con señal de riesgo", eye_ref_note: "※ Los valores por ojo de una foto del rostro son orientativos; un primer plano del ojo es más preciso.",
        loading_elapsed: "{s} s transcurridos",
        gemma_idle: "Completa primero el análisis de IA para ver aquí tu opinión personalizada.", rep_followup_title: "🤖 Haz más preguntas a la IA", rep_followup_ph: "ej. ¿Cómo cuido mis ojos?",
        srv_err: "⚠️ No se puede conectar con el servidor.", nextq_fallback: "¿Hay algo más que le moleste en los ojos?",
        survey_done: "Encuesta básica completada. Generando una pregunta personalizada... ⏳", next_q_generating: "Generando la siguiente pregunta personalizada... ⏳", symptom_extra: "Síntoma sospechoso adicional encontrado",
        opinion_writing: "La IA está redactando su informe... ✍️\n\n", opinion_error: "⚠️ Se perdió la conexión con el servidor de IA local.",
        notif_title: "Diagnóstico Eye-Catch completado 🏥", notif_body: "¡Su informe de IA personalizado está listo! Revise sus resultados.", followup_thinking: "Pensando una respuesta... 🤔\n\n",
        pdf_doc_title: "Informe Diagnóstico Eye-Catch", pdf_issued: "Fecha de emisión", pdf_s1: "1. Análisis de Cataratas por IA", pdf_s2: "2. Autoprueba Macular (Rejilla de Amsler)", pdf_s3: "3. Hallazgos de la Encuesta IA", pdf_s4: "4. Opinión Integral de IA (Powered by Gemma)",
        pdf_footer: "Este informe es una ayuda de autodetección asistida por IA.<br>Consulte a un oftalmólogo para un diagnóstico y tratamiento precisos."
    },
    fr: {
        nav_test: "Analyse IA", nav_disease: "Maladies", nav_report: "Rapport", nav_map: "Trouver Clinique",
        intro_title: "Votre santé oculaire,<br>protégée par l'IA", intro_desc: "Analyse photo et sondage pour détecter les risques oculaires.",
        start_btn: "Démarrer l'analyse", upload_title: "Télécharger Photo", upload_btn: "Sélectionner Photo",
        guide_title: "⚠️ Guide", guide_list: "<li>Regardez de face.</li><li>Évitez les reflets.</li>",
        tips_title: "Conseils photo pour<br>une analyse précise", tip1_t: "Utilisez la caméra arrière !", tip1_d: "La caméra arrière offre une meilleure qualité et moins de reflets.", tip2_t: "Activez le flash", tip2_d: "Le flash dans un endroit lumineux donne des résultats plus précis.", tip3_t: "Gardez environ 30 cm de distance", tip3_d: "Trop près, la photo peut être floue.", tips_btn: "Compris !",
        loading_title: "IA en analyse...", ai_res_title: "Résultat Cataracte", next_amsler: "Étape 2: Macula",
        ams_title: "Test de la grille d'Amsler", ams_ok: "Normal (Droit)", ams_bad: "Déformé/Tache",
        chat_yes: "Oui", chat_no: "Non", dis_main_title: "Maladies Oculaires", rep_title: "Rapport de Diagnostic Eye-Catch",
        rep_l1: "1. IA Cataracte", rep_l2: "2. Test Maculaire", rep_l3: "3. Sondage", rep_l4: "4. Avis de Gemma AI ✨", pdf_btn: "📄 Télécharger PDF", map_btn: "🌎 Trouver Clinique (Google)",
        msg_gen: "Génération du rapport...", res_ams_bad: "Distorsion", res_ams_ok: "Normal", res_chat_none: "Aucun symptôme",
        rep_warn: "Outil assisté par IA. Veuillez consulter un ophtalmologiste.",
        dis_card_hint: "Appuyez sur une carte pour voir la description complète.", dis_more: "En savoir plus →", dis_modal_note: "Si vous remarquez ces symptômes, consultez un ophtalmologiste.", dm_close: "Fermer", dis_ai_badge: "Analyse par IA",
        map_page_title: "Trouver une clinique près de chez vous", map_locate: "📍 Utiliser ma position", map_open_full: "Ouvrir la carte complète",
        map_status_idle: "Appuyez sur le bouton pour trouver des cliniques proches.", map_status_loading: "Localisation...", map_status_denied: "Position refusée. Recherchez sur la carte complète.", map_status_unsupported: "Ce navigateur ne prend pas en charge la géolocalisation.",
        map_you: "📍 Vous êtes ici", map_searching: "Recherche de cliniques proches... ⏳", map_found: "{n} clinique(s) ophtalmologique(s) à proximité.", map_none: "Aucune clinique trouvée à proximité. Utilisez la carte complète.", map_search_err: "Échec de la recherche. Utilisez la carte complète.", map_directions: "Itinéraire",
        ai_normal: "Aucune anomalie notable (Normal)", ai_risk: "Stade de risque de cataracte (Examen approfondi recommandé)", ai_borderline: "Résultat limite (Reprenez la photo ou envisagez un examen ophtalmologique)", ai_invalid: "Cela ne ressemble pas à une photo d'œil. Veuillez téléverser un gros plan de votre œil.",
        face_mode_note: "👁 {n} œil/yeux détecté(s) sur la photo du visage et analysé(s).",
        eye_breakdown_title: "Analyse par œil (selon la photo)", eye_left: "Œil gauche", eye_right: "Œil droit", eye_unilateral: "⚠️ Possiblement unilatéral — un seul œil signalé", eye_ref_note: "※ Les valeurs par œil issues d'une photo du visage sont indicatives ; un gros plan de l'œil est plus précis.",
        loading_elapsed: "{s} s écoulées",
        gemma_idle: "Effectuez d'abord l'analyse IA pour voir votre avis personnalisé ici.", rep_followup_title: "🤖 Posez plus de questions à l'IA", rep_followup_ph: "ex. Comment prendre soin de mes yeux ?",
        srv_err: "⚠️ Impossible de se connecter au serveur.", nextq_fallback: "Y a-t-il autre chose qui vous gêne aux yeux ?",
        survey_done: "Questionnaire de base terminé. Génération d'une question personnalisée... ⏳", next_q_generating: "Génération de la prochaine question personnalisée... ⏳", symptom_extra: "Symptôme suspect supplémentaire détecté",
        opinion_writing: "L'IA rédige votre avis... ✍️\n\n", opinion_error: "⚠️ La connexion au serveur IA local a été perdue.",
        notif_title: "Diagnostic Eye-Catch terminé 🏥", notif_body: "Votre avis IA personnalisé est prêt ! Consultez vos résultats.", followup_thinking: "Réflexion à une réponse... 🤔\n\n",
        pdf_doc_title: "Rapport de Diagnostic Eye-Catch", pdf_issued: "Date d'émission", pdf_s1: "1. Analyse Cataracte par IA", pdf_s2: "2. Autotest Maculaire (Grille d'Amsler)", pdf_s3: "3. Conclusions du Questionnaire IA", pdf_s4: "4. Avis Global de l'IA (Powered by Gemma)",
        pdf_footer: "Ce rapport est une aide d'auto-dépistage assistée par IA.<br>Veuillez consulter un ophtalmologiste pour un diagnostic et un traitement précis."
    },
    ja: {
        nav_test: "AI検査", nav_disease: "眼疾患について", nav_report: "診断レポート", nav_map: "病院検索",
        intro_title: "あなたの目の健康、<br>AIがお守りします", intro_desc: "AI写真分析と問診で主要な眼疾患のリスクをチェックします。",
        start_btn: "検査開始", upload_title: "写真アップロード", upload_btn: "写真を選択して送信",
        guide_title: "⚠️ 正確な分析のために", guide_list: "<li>正面から撮影してください。</li><li>光の反射に注意してください。</li>",
        tips_title: "正確な分析のための<br>撮影のコツ", tip1_t: "前面より背面カメラで！", tip1_d: "背面カメラの方が画質が良く、光の反射も少ないです。", tip2_t: "フラッシュをオンに", tip2_d: "明るい場所でフラッシュを使うとより正確です。", tip3_t: "30cmの距離を保って", tip3_d: "近すぎるとピントがぼやけることがあります。", tips_btn: "わかりました！",
        loading_title: "AI分析中...", ai_res_title: "白内障判定結果", next_amsler: "ステップ2：黄斑変性テスト",
        ams_title: "アムスラーグリッドテスト", ams_ok: "正常（まっすぐ）", ams_bad: "歪み/暗点",
        chat_yes: "はい", chat_no: "いいえ", dis_main_title: "4大眼疾患について", rep_title: "Eye-Catch 診断レポート",
        rep_l1: "1. 白内障AI結果", rep_l2: "2. 黄斑変性結果", rep_l3: "3. 問診結果", rep_l4: "4. Gemma AIカスタム所見 ✨", pdf_btn: "📄 PDFダウンロード", map_btn: "🌎 病院を探す (Google)",
        msg_gen: "レポートを作成中...", res_ams_bad: "異常あり（要検査）", res_ams_ok: "特記事項なし", res_chat_none: "主要な症状なし",
        rep_warn: "本レポートはAIによる補助資料です。正確な診断のため眼科を受診してください。",
        dis_card_hint: "カードをタップすると詳しい説明が見られます。", dis_more: "詳しく見る →", dis_modal_note: "このような症状があれば眼科を受診してください。", dm_close: "閉じる", dis_ai_badge: "AI分析対応",
        map_page_title: "近くの眼科を探す", map_locate: "📍 現在地で探す", map_open_full: "地図全体を開く",
        map_status_idle: "下のボタンを押して近くの眼科を探しましょう。", map_status_loading: "現在地を確認中...", map_status_denied: "位置情報が拒否されました。地図全体で検索してください。", map_status_unsupported: "このブラウザは位置情報に対応していません。",
        map_you: "📍 現在地", map_searching: "近くの眼科を検索中... ⏳", map_found: "近くに眼科が{n}件見つかりました。", map_none: "近くに眼科が見つかりませんでした。地図全体で検索してください。", map_search_err: "検索に失敗しました。地図全体で検索してください。", map_directions: "経路",
        ai_normal: "特記所見なし（正常）", ai_risk: "白内障リスク段階（精密検査を推奨）", ai_borderline: "境界域（再撮影または眼科検診を推奨）", ai_invalid: "目の写真ではないようです。目のクローズアップ写真をアップロードしてください。",
        face_mode_note: "👁 顔写真から目を{n}箇所検出して分析しました。",
        eye_breakdown_title: "目ごとの分析（写真基準）", eye_left: "左目", eye_right: "右目", eye_unilateral: "⚠️ 片側の疑い — 片方の目だけ危険信号", eye_ref_note: "※ 顔写真の目ごとの数値は参考用で、目のクローズアップ撮影の方が精度が高いです。",
        loading_elapsed: "{s}秒経過",
        gemma_idle: "先にAI検査を完了すると、ここにカスタム所見が表示されます。", rep_followup_title: "🤖 AIにもっと質問する", rep_followup_ph: "例：ケア方法を教えて",
        srv_err: "⚠️ サーバーに接続できません。", nextq_fallback: "他に目で気になるところはありますか？",
        survey_done: "基本問診が完了しました。カスタム追加質問を生成中です... ⏳", next_q_generating: "次のカスタム質問を生成中です... ⏳", symptom_extra: "その他の疑わしい症状を追加検出",
        opinion_writing: "AIが所見を作成中です... ✍️\n\n", opinion_error: "⚠️ ローカルAIサーバーとの接続が切れました。",
        notif_title: "Eye-Catch 診断完了 🏥", notif_body: "AIによるカスタム所見が完成しました！結果をご確認ください。", followup_thinking: "回答を考えています... 🤔\n\n",
        pdf_doc_title: "Eye-Catch 精密診断レポート", pdf_issued: "発行日", pdf_s1: "1. 白内障 AI 分析結果", pdf_s2: "2. 黄斑自己検査（アムスラーグリッド）", pdf_s3: "3. AI問診の主な所見", pdf_s4: "4. 総合AI所見（Powered by Gemma）",
        pdf_footer: "本レポートはAIによる自己スクリーニング補助資料です。<br>正確な診断と治療のため、必ず眼科医にご相談ください。"
    },
    zh: {
        nav_test: "AI检测", nav_disease: "疾病介绍", nav_report: "诊断报告", nav_map: "寻找医院",
        intro_title: "您的眼部健康，<br>由AI来守护", intro_desc: "通过AI照片分析和问卷调查检查主要眼部疾病风险。",
        start_btn: "开始检测", upload_title: "上传照片", upload_btn: "选择并发送照片",
        guide_title: "⚠️ 准确分析指南", guide_list: "<li>请正面拍摄。</li><li>请注意避免反光。</li>",
        tips_title: "拍摄小技巧<br>让分析更准确", tip1_t: "请使用后置摄像头！", tip1_d: "后置摄像头画质更好，反光更少。", tip2_t: "请打开闪光灯", tip2_d: "在明亮的地方使用闪光灯，结果更准确。", tip3_t: "保持约30厘米距离", tip3_d: "太近可能会导致焦点模糊。", tips_btn: "明白了！",
        loading_title: "AI分析中...", ai_res_title: "白内障判定结果", next_amsler: "第二步：黄斑变性测试",
        ams_title: "阿姆斯勒方格表", ams_ok: "正常（线条笔直）", ams_bad: "扭曲/黑影",
        chat_yes: "是", chat_no: "否", dis_main_title: "四大眼疾介绍", rep_title: "Eye-Catch 综合诊断报告",
        rep_l1: "1. 白内障AI结果", rep_l2: "2. 黄斑变性结果", rep_l3: "3. 问卷结果", rep_l4: "4. Gemma AI 个性化意见 ✨", pdf_btn: "📄 下载 PDF", map_btn: "🌎 寻找医院 (Google)",
        msg_gen: "正在生成报告...", res_ams_bad: "发现异常", res_ams_ok: "正常", res_chat_none: "无主要症状",
        rep_warn: "本报告为AI辅助参考资料，为了获得准确诊断，请咨询眼科医生。",
        dis_card_hint: "点击卡片可查看详细说明。", dis_more: "查看详情 →", dis_modal_note: "如有这些症状，请及时就诊眼科。", dm_close: "关闭", dis_ai_badge: "支持AI分析",
        map_page_title: "查找附近的眼科", map_locate: "📍 使用我的位置", map_open_full: "打开完整地图",
        map_status_idle: "点击下方按钮查找附近的眼科。", map_status_loading: "正在确认位置...", map_status_denied: "位置权限被拒绝，请在完整地图中搜索。", map_status_unsupported: "此浏览器不支持定位功能。",
        map_you: "📍 我的位置", map_searching: "正在搜索附近的眼科... ⏳", map_found: "在附近找到 {n} 家眼科。", map_none: "附近未找到眼科，请在完整地图中搜索。", map_search_err: "搜索失败，请使用完整地图。", map_directions: "路线",
        ai_normal: "无明显异常（正常）", ai_risk: "白内障风险阶段（建议精密检查）", ai_borderline: "临界阶段（建议重新拍摄或进行眼科检查）", ai_invalid: "这看起来不像眼睛照片。请上传眼部特写照片。",
        face_mode_note: "👁 已从面部照片中检测到{n}处眼睛并进行分析。",
        eye_breakdown_title: "逐眼分析（以照片为准）", eye_left: "左眼", eye_right: "右眼", eye_unilateral: "⚠️ 疑似单侧 — 仅一只眼出现风险信号", eye_ref_note: "※ 面部照片的逐眼数值仅供参考，眼部特写拍摄的准确度更高。",
        loading_elapsed: "已用时 {s} 秒",
        gemma_idle: "请先完成 AI 检测，个性化意见将显示在这里。", rep_followup_title: "🤖 向 AI 提出更多问题", rep_followup_ph: "例：如何护理眼睛？",
        srv_err: "⚠️ 无法连接到服务器。", nextq_fallback: "您的眼睛还有其他不适吗？",
        survey_done: "基础问诊已完成。正在生成个性化追加问题... ⏳", next_q_generating: "正在生成下一个个性化问题... ⏳", symptom_extra: "发现其他可疑症状",
        opinion_writing: "AI正在撰写意见书... ✍️\n\n", opinion_error: "⚠️ 与本地AI服务器的连接已断开。",
        notif_title: "Eye-Catch 诊断完成 🏥", notif_body: "AI个性化意见书已完成！请查看您的结果。", followup_thinking: "正在思考答案... 🤔\n\n",
        pdf_doc_title: "Eye-Catch 精密诊断报告", pdf_issued: "签发日期", pdf_s1: "1. 白内障 AI 分析结果", pdf_s2: "2. 黄斑自测（阿姆斯勒方格表）", pdf_s3: "3. AI问诊主要发现", pdf_s4: "4. 综合AI意见书（Powered by Gemma）",
        pdf_footer: "本报告为AI辅助的自我筛查参考资料。<br>为获得准确的诊断和治疗，请务必咨询眼科医生。"
    }
};

// code: 언어 중립 질환 키 (백엔드 RAG 검색용 — 0=녹내장, 1=당뇨망막병증)
const questions = {
    ko: [{t:'주변 시야가 답답하게 좁아진 느낌인가요?',type:'녹내장 의심',code:'glaucoma'},{t:'눈앞에 실오라기 같은 것들이 떠다니나요?',type:'당뇨망막병증 의심',code:'retinopathy'}],
    en: [{t:'Does your peripheral vision feel restricted?',type:'Glaucoma Suspect',code:'glaucoma'},{t:'Do you see floaters in your vision?',type:'Retinopathy Suspect',code:'retinopathy'}],
    es: [{t:'¿Siente que su visión periférica está restringida?',type:'Sospecha de Glaucoma',code:'glaucoma'},{t:'¿Ve moscas volantes (manchas) en su visión?',type:'Sospecha de Retinopatía',code:'retinopathy'}],
    fr: [{t:'Votre vision périphérique vous semble-t-elle restreinte?',type:'Suspicion de Glaucome',code:'glaucoma'},{t:'Voyez-vous des corps flottants dans votre vision?',type:'Suspicion de Rétinopathie',code:'retinopathy'}],
    ja: [{t:'周辺の視野が狭く感じますか？',type:'緑内障の疑い',code:'glaucoma'},{t:'目の前に糸くずのようなものが飛んで見えますか？',type:'糖尿病網膜症の疑い',code:'retinopathy'}],
    zh: [{t:'您感觉周边视野变窄了吗？',type:'疑似青光眼',code:'glaucoma'},{t:'您眼前有像线头一样飘动的东西吗？',type:'疑似糖尿病视网膜病变',code:'retinopathy'}]
};

// ==========================================
// 질환 소개 데이터 (app-disease.js의 renderDiseases가 소비)
// ==========================================
const diseaseData = {
    ko: [
        {t:"백내장",   d:"수정체가 투명성을 잃고 하얗게 혼탁해지는 질환으로 노화가 주된 원인입니다. 시야 흐림, 빛 번짐이 주요 증상입니다.", i:"🌫️"},
        {t:"황반변성", d:"망막 중심부 황반이 손상되어 직선이 휘어 보이거나 중심부가 까맣게 보이는 실명 유발 질환입니다.", i:"🎯"},
        {t:"녹내장",   d:"안압 상승으로 시신경이 손상되어 시야가 주변부부터 좁아지는 소리 없는 시력 도둑입니다.", i:"🌑"},
        {t:"당뇨망막병증", d:"당뇨 합병증으로 망막 혈관이 손상되어 비문증(날파리증)이나 시력 저하가 발생합니다.", i:"🩸"}
    ],
    en: [
        {t:"Cataract",            d:"Clouding of the lens leading to blurred vision and glare, primarily caused by aging.", i:"🌫️"},
        {t:"Macular Degeneration",d:"Damage to the macula causing distorted lines or a black spot in central vision.", i:"🎯"},
        {t:"Glaucoma",            d:"Optic nerve damage often from high eye pressure, leading to narrowing peripheral vision.", i:"🌑"},
        {t:"Diabetic Retinopathy",d:"Diabetes complication affecting retinal blood vessels, causing floaters and vision loss.", i:"🩸"}
    ],
    es: [
        {t:"Cataratas",              d:"Opacidad del cristalino que causa visión borrosa y deslumbramiento, causada principalmente por el envejecimiento.", i:"🌫️"},
        {t:"Degeneración Macular",   d:"Daño en la mácula que causa líneas distorsionadas o una mancha negra en la visión central.", i:"🎯"},
        {t:"Glaucoma",               d:"Daño en el nervio óptico por presión alta, lo que reduce la visión periférica.", i:"🌑"},
        {t:"Retinopatía Diabética",  d:"Complicación de la diabetes que afecta los vasos sanguíneos de la retina.", i:"🩸"}
    ],
    fr: [
        {t:"Cataracte",                  d:"Opacification du cristallin entraînant une vision floue, principalement causée par le vieillissement.", i:"🌫️"},
        {t:"Dégénérescence Maculaire",   d:"Lésion de la macula déformant la vision centrale (lignes ondulées ou tache noire).", i:"🎯"},
        {t:"Glaucome",                   d:"Lésion du nerf optique due à une pression élevée, réduisant la vision périphérique.", i:"🌑"},
        {t:"Rétinopathie Diabétique",    d:"Complication du diabète affectant les vaisseaux sanguins de la rétine.", i:"🩸"}
    ],
    ja: [
        {t:"白内障",       d:"水晶体が濁り、視界がかすんだり光がまぶしく感じたりする老化が主な原因の疾患です。", i:"🌫️"},
        {t:"黄斑変性",     d:"網膜の中心部が損傷し、線が歪んで見えたり中心部が暗く見えたりする疾患です。", i:"🎯"},
        {t:"緑内障",       d:"眼圧上昇により視神経が損傷し、周辺の視野から徐々に狭くなる疾患です。", i:"🌑"},
        {t:"糖尿病網膜症", d:"糖尿病の合併症で網膜の血管が損傷し、飛蚊症や視力低下を引き起こします。", i:"🩸"}
    ],
    zh: [
        {t:"白内障",          d:"晶状体浑浊导致视力模糊和眩光，主要由衰老引起。", i:"🌫️"},
        {t:"黄斑变性",        d:"黄斑受损导致中心视力扭曲或出现黑点。", i:"🎯"},
        {t:"青光眼",          d:"视神经受损，通常由高眼压引起，导致周边视野变窄。", i:"🌑"},
        {t:"糖尿病视网膜病变",d:"糖尿病并发症影响视网膜血管，导致飞蚊症和视力下降。", i:"🩸"}
    ]
};
// ==========================================================================
// 확장 문자열 (시력·대비감도 검사 / 위험도 문진 / 행동 권고 / 동의)
// 기존 6개 언어 객체를 직접 수정하는 대신 여기서 병합한다 — 추가/검토가 쉽고
// 누락된 언어가 있으면 병합 시점에 콘솔로 바로 드러난다.
// ==========================================================================
const extraStrings = {
  ko: {
    nav_vision: "시력 검사",
    vt_title: "시력 · 대비감도 자가검사", vt_start: "검사 시작",
    vt_calib_title: "1단계 · 화면 크기 맞추기",
    vt_calib_desc: "카드(신용/체크/신분증)를 화면에 대고 사각형을 실물과 같은 크기로 맞추세요. 국제 규격이라 어느 카드든 됩니다.",
    vt_calib_edge_long: "긴 변 85.6mm", vt_calib_edge_short: "짧은 변 54.0mm",
    vt_calib_save: "저장하고 계속", vt_calib_done: "화면 보정 완료",
    vt_calib_verify: "확인: 아래 막대가 자로 정확히 50mm면 보정이 맞습니다.",
    vt_eye_left: "왼쪽 눈", vt_eye_right: "오른쪽 눈",
    vt_cover_left: "왼쪽 눈을 손으로 가려주세요", vt_cover_right: "오른쪽 눈을 손으로 가려주세요",
    vt_acuity: "시력", vt_contrast: "대비감도",
    vt_acuity_desc: "E가 향하는 방향을 고르세요. 점점 작아집니다.",
    vt_contrast_desc: "E가 점점 흐려집니다. 보이는 동안 방향을 고르세요.",
    vt_begin: "준비됐어요", vt_which_dir: "E가 향하는 방향은?",
    vt_result_title: "기능검사 결과", vt_redo: "다시 검사",
    vt_need_calib: "먼저 화면 크기 맞추기를 완료해주세요.",
    vt_asym: "⚠️ 좌우 차이가 큽니다 — 한쪽 눈만 진행된 변화일 수 있어 안과 확인을 권합니다.",
    q_age: "연령대를 알려주세요.", q_diabetes: "당뇨가 있으신가요?",
    q_hypertension: "고혈압이 있으신가요?", q_family: "가족 중 녹내장·황반변성 진단을 받은 분이 있나요?",
    q_smoking: "현재 흡연 중이신가요?",
    age_under40: "40세 미만", age_40s: "40–49세", age_50s: "50–59세", age_60s: "60–69세", age_70plus: "70세 이상",
    risk_diabetes: "당뇨", risk_hypertension: "고혈압", risk_family: "가족력", risk_smoking: "흡연",
    tri_title: "권장 조치", tri_now: "빠른 시일 내 안과 진료를 권합니다",
    tri_weeks: "수 주 내 안과 검진을 권합니다", tri_monitor: "정기 검진으로 경과를 관찰하세요",
    tri_now_why: "위험 소견과 위험요인이 함께 확인됐습니다.",
    tri_weeks_why: "경계 소견이나 위험요인이 확인됐습니다.",
    tri_monitor_why: "현재 특별한 위험 신호는 없습니다.",
    ams_which_left: "왼쪽 눈 검사 — 오른쪽 눈을 가리고 중앙 점을 보세요",
    ams_which_right: "오른쪽 눈 검사 — 왼쪽 눈을 가리고 중앙 점을 보세요",
    ams_result_both: "양쪽 정상", ams_result_left: "왼쪽 눈 이상", ams_result_right: "오른쪽 눈 이상", ams_result_bad: "양쪽 이상",
    consent_title: "결과 저장 동의", consent_agree: "동의하고 저장", consent_skip: "저장하지 않기",
    consent_text: "검사 결과와 AI 참고 정보를 서버에 저장합니다. 건강정보는 민감정보이므로 동의하신 경우에만 저장하며, 사진은 저장하지 않습니다.",
    rep_info_title: "AI 참고 정보", info_writing: "AI가 참고 정보를 정리하고 있습니다"
  },
  en: {
    nav_vision: "Vision Test",
    vt_title: "Visual Acuity & Contrast Test", vt_start: "Start test",
    vt_calib_title: "Step 1 · Match your screen size",
    vt_calib_desc: "Hold any card (credit/debit/ID) against the screen and resize the rectangle to match. Cards are a fixed international size.",
    vt_calib_edge_long: "Long edge 85.6mm", vt_calib_edge_short: "Short edge 54.0mm",
    vt_calib_save: "Save and continue", vt_calib_done: "Screen calibrated",
    vt_calib_verify: "Check: the bar below should measure exactly 50mm with a ruler.",
    vt_eye_left: "Left eye", vt_eye_right: "Right eye",
    vt_cover_left: "Cover your left eye", vt_cover_right: "Cover your right eye",
    vt_acuity: "Acuity", vt_contrast: "Contrast sensitivity",
    vt_acuity_desc: "Pick the direction the E points. It gets smaller each round.",
    vt_contrast_desc: "The E gets fainter. Pick its direction while you can still see it.",
    vt_begin: "I am ready", vt_which_dir: "Which way does the E point?",
    vt_result_title: "Functional test results", vt_redo: "Test again",
    vt_need_calib: "Please complete screen calibration first.",
    vt_asym: "⚠️ Large difference between eyes — this may indicate one-sided change. An eye exam is recommended.",
    q_age: "What is your age range?", q_diabetes: "Do you have diabetes?",
    q_hypertension: "Do you have high blood pressure?", q_family: "Has a family member been diagnosed with glaucoma or macular degeneration?",
    q_smoking: "Do you currently smoke?",
    age_under40: "Under 40", age_40s: "40–49", age_50s: "50–59", age_60s: "60–69", age_70plus: "70+",
    risk_diabetes: "Diabetes", risk_hypertension: "Hypertension", risk_family: "Family history", risk_smoking: "Smoking",
    tri_title: "Recommended action", tri_now: "See an ophthalmologist soon",
    tri_weeks: "Schedule an eye exam within a few weeks", tri_monitor: "Monitor with routine check-ups",
    tri_now_why: "Both a concerning finding and risk factors were identified.",
    tri_weeks_why: "A borderline finding or risk factors were identified.",
    tri_monitor_why: "No particular warning signs right now.",
    ams_which_left: "Left eye — cover your right eye and look at the center dot",
    ams_which_right: "Right eye — cover your left eye and look at the center dot",
    ams_result_both: "Both normal", ams_result_left: "Left eye abnormal", ams_result_right: "Right eye abnormal", ams_result_bad: "Both abnormal",
    consent_title: "Consent to save results", consent_agree: "Agree and save", consent_skip: "Do not save",
    consent_text: "Your results and the AI reference notes will be stored on the server. Health data is sensitive, so we store it only with your consent. Photos are never stored.",
    rep_info_title: "AI reference notes", info_writing: "The AI is preparing reference notes"
  },
  es: {
    nav_vision: "Test visual",
    vt_title: "Test de agudeza y sensibilidad al contraste", vt_start: "Comenzar",
    vt_calib_title: "Paso 1 · Ajuste el tamaño de pantalla",
    vt_calib_desc: "Ponga una tarjeta (crédito/débito/identificación) sobre la pantalla y ajuste el rectángulo. Las tarjetas tienen tamaño internacional fijo.",
    vt_calib_edge_long: "Lado largo 85,6mm", vt_calib_edge_short: "Lado corto 54,0mm",
    vt_calib_save: "Guardar y continuar", vt_calib_done: "Pantalla calibrada",
    vt_calib_verify: "Compruebe: la barra inferior debe medir exactamente 50mm con una regla.",
    vt_eye_left: "Ojo izquierdo", vt_eye_right: "Ojo derecho",
    vt_cover_left: "Cúbrase el ojo izquierdo", vt_cover_right: "Cúbrase el ojo derecho",
    vt_acuity: "Agudeza", vt_contrast: "Sensibilidad al contraste",
    vt_acuity_desc: "Elija hacia dónde apunta la E. Se hará más pequeña.",
    vt_contrast_desc: "La E se hará más tenue. Elija su dirección mientras la vea.",
    vt_begin: "Estoy listo", vt_which_dir: "¿Hacia dónde apunta la E?",
    vt_result_title: "Resultados funcionales", vt_redo: "Repetir test",
    vt_need_calib: "Complete primero la calibración de pantalla.",
    vt_asym: "⚠️ Gran diferencia entre ojos — puede indicar un cambio unilateral. Se recomienda examen ocular.",
    q_age: "¿Cuál es su rango de edad?", q_diabetes: "¿Tiene diabetes?",
    q_hypertension: "¿Tiene hipertensión?", q_family: "¿Algún familiar fue diagnosticado con glaucoma o degeneración macular?",
    q_smoking: "¿Fuma actualmente?",
    age_under40: "Menos de 40", age_40s: "40–49", age_50s: "50–59", age_60s: "60–69", age_70plus: "70+",
    risk_diabetes: "Diabetes", risk_hypertension: "Hipertensión", risk_family: "Antecedentes familiares", risk_smoking: "Tabaquismo",
    tri_title: "Acción recomendada", tri_now: "Consulte a un oftalmólogo pronto",
    tri_weeks: "Programe un examen ocular en unas semanas", tri_monitor: "Controle con revisiones periódicas",
    tri_now_why: "Se identificaron un hallazgo preocupante y factores de riesgo.",
    tri_weeks_why: "Se identificó un hallazgo límite o factores de riesgo.",
    tri_monitor_why: "Sin señales de alerta por ahora.",
    ams_which_left: "Ojo izquierdo — cúbrase el derecho y mire el punto central",
    ams_which_right: "Ojo derecho — cúbrase el izquierdo y mire el punto central",
    ams_result_both: "Ambos normales", ams_result_left: "Ojo izquierdo anormal", ams_result_right: "Ojo derecho anormal", ams_result_bad: "Ambos anormales",
    consent_title: "Consentimiento para guardar", consent_agree: "Aceptar y guardar", consent_skip: "No guardar",
    consent_text: "Sus resultados y las notas de referencia de la IA se guardarán en el servidor. Los datos de salud son sensibles, así que solo se guardan con su consentimiento. Las fotos nunca se guardan.",
    rep_info_title: "Notas de referencia de la IA", info_writing: "La IA está preparando las notas"
  },
  fr: {
    nav_vision: "Test visuel",
    vt_title: "Test d'acuité et de sensibilité au contraste", vt_start: "Commencer",
    vt_calib_title: "Étape 1 · Calibrer la taille de l'écran",
    vt_calib_desc: "Placez une carte (crédit/débit/identité) sur l'écran et ajustez le rectangle. Les cartes ont une taille internationale fixe.",
    vt_calib_edge_long: "Grand côté 85,6mm", vt_calib_edge_short: "Petit côté 54,0mm",
    vt_calib_save: "Enregistrer et continuer", vt_calib_done: "Écran calibré",
    vt_calib_verify: "Vérifiez : la barre ci-dessous doit mesurer exactement 50mm avec une règle.",
    vt_eye_left: "Œil gauche", vt_eye_right: "Œil droit",
    vt_cover_left: "Couvrez votre œil gauche", vt_cover_right: "Couvrez votre œil droit",
    vt_acuity: "Acuité", vt_contrast: "Sensibilité au contraste",
    vt_acuity_desc: "Choisissez la direction du E. Il devient plus petit.",
    vt_contrast_desc: "Le E devient plus pâle. Choisissez sa direction tant que vous le voyez.",
    vt_begin: "Je suis prêt", vt_which_dir: "Dans quelle direction pointe le E ?",
    vt_result_title: "Résultats fonctionnels", vt_redo: "Refaire le test",
    vt_need_calib: "Veuillez d'abord calibrer l'écran.",
    vt_asym: "⚠️ Grande différence entre les yeux — cela peut indiquer une atteinte unilatérale. Un examen est recommandé.",
    q_age: "Quelle est votre tranche d'âge ?", q_diabetes: "Êtes-vous diabétique ?",
    q_hypertension: "Avez-vous de l'hypertension ?", q_family: "Un proche a-t-il été diagnostiqué d'un glaucome ou d'une DMLA ?",
    q_smoking: "Fumez-vous actuellement ?",
    age_under40: "Moins de 40", age_40s: "40–49", age_50s: "50–59", age_60s: "60–69", age_70plus: "70+",
    risk_diabetes: "Diabète", risk_hypertension: "Hypertension", risk_family: "Antécédents familiaux", risk_smoking: "Tabagisme",
    tri_title: "Action recommandée", tri_now: "Consultez un ophtalmologiste rapidement",
    tri_weeks: "Planifiez un examen dans quelques semaines", tri_monitor: "Surveillez lors des contrôles réguliers",
    tri_now_why: "Un signe préoccupant et des facteurs de risque ont été identifiés.",
    tri_weeks_why: "Un résultat limite ou des facteurs de risque ont été identifiés.",
    tri_monitor_why: "Aucun signal d'alerte particulier pour le moment.",
    ams_which_left: "Œil gauche — couvrez le droit et fixez le point central",
    ams_which_right: "Œil droit — couvrez le gauche et fixez le point central",
    ams_result_both: "Les deux normaux", ams_result_left: "Œil gauche anormal", ams_result_right: "Œil droit anormal", ams_result_bad: "Les deux anormaux",
    consent_title: "Consentement à l'enregistrement", consent_agree: "Accepter et enregistrer", consent_skip: "Ne pas enregistrer",
    consent_text: "Vos résultats et les notes de référence de l'IA seront enregistrés sur le serveur. Les données de santé étant sensibles, l'enregistrement n'a lieu qu'avec votre consentement. Les photos ne sont jamais enregistrées.",
    rep_info_title: "Notes de référence de l'IA", info_writing: "L'IA prépare les notes de référence"
  },
  ja: {
    nav_vision: "視力検査",
    vt_title: "視力・コントラスト感度セルフチェック", vt_start: "検査を開始",
    vt_calib_title: "ステップ1・画面サイズの調整",
    vt_calib_desc: "カード(クレジット/キャッシュ/身分証)を画面に当て、四角形を実物と同じ大きさに合わせてください。カードは国際規格で固定サイズです。",
    vt_calib_edge_long: "長辺 85.6mm", vt_calib_edge_short: "短辺 54.0mm",
    vt_calib_save: "保存して続ける", vt_calib_done: "画面調整完了",
    vt_calib_verify: "確認: 下のバーが定規でちょうど50mmなら調整は正しいです。",
    vt_eye_left: "左目", vt_eye_right: "右目",
    vt_cover_left: "左目を手で覆ってください", vt_cover_right: "右目を手で覆ってください",
    vt_acuity: "視力", vt_contrast: "コントラスト感度",
    vt_acuity_desc: "Eの向きを選んでください。だんだん小さくなります。",
    vt_contrast_desc: "Eが薄くなっていきます。見える間に向きを選んでください。",
    vt_begin: "準備できました", vt_which_dir: "Eはどの向き？",
    vt_result_title: "機能検査の結果", vt_redo: "もう一度検査",
    vt_need_calib: "先に画面サイズの調整を完了してください。",
    vt_asym: "⚠️ 左右差が大きいです — 片眼だけの変化の可能性があり、眼科受診をお勧めします。",
    q_age: "年代を教えてください。", q_diabetes: "糖尿病はありますか？",
    q_hypertension: "高血圧はありますか？", q_family: "ご家族に緑内障・黄斑変性と診断された方はいますか？",
    q_smoking: "現在喫煙していますか？",
    age_under40: "40歳未満", age_40s: "40–49歳", age_50s: "50–59歳", age_60s: "60–69歳", age_70plus: "70歳以上",
    risk_diabetes: "糖尿病", risk_hypertension: "高血圧", risk_family: "家族歴", risk_smoking: "喫煙",
    tri_title: "推奨される対応", tri_now: "早めに眼科を受診してください",
    tri_weeks: "数週間以内に眼科検診を受けてください", tri_monitor: "定期検診で経過を観察してください",
    tri_now_why: "懸念される所見と危険因子の両方が確認されました。",
    tri_weeks_why: "境界域の所見または危険因子が確認されました。",
    tri_monitor_why: "現時点で特別な警告サインはありません。",
    ams_which_left: "左目の検査 — 右目を覆って中央の点を見てください",
    ams_which_right: "右目の検査 — 左目を覆って中央の点を見てください",
    ams_result_both: "両眼正常", ams_result_left: "左目に異常", ams_result_right: "右目に異常", ams_result_bad: "両眼に異常",
    consent_title: "結果保存の同意", consent_agree: "同意して保存", consent_skip: "保存しない",
    consent_text: "検査結果とAI参考情報をサーバーに保存します。健康情報は機微情報のため、同意いただいた場合のみ保存し、写真は保存しません。",
    rep_info_title: "AI参考情報", info_writing: "AIが参考情報をまとめています"
  },
  zh: {
    nav_vision: "视力检查",
    vt_title: "视力与对比敏感度自测", vt_start: "开始检查",
    vt_calib_title: "第1步 · 校准屏幕尺寸",
    vt_calib_desc: "把任意卡片(信用卡/借记卡/身份证)贴在屏幕上，调整矩形至与实物一致。卡片为国际统一尺寸。",
    vt_calib_edge_long: "长边 85.6mm", vt_calib_edge_short: "短边 54.0mm",
    vt_calib_save: "保存并继续", vt_calib_done: "屏幕校准完成",
    vt_calib_verify: "验证：用尺子量下方色条，应恰好为50mm。",
    vt_eye_left: "左眼", vt_eye_right: "右眼",
    vt_cover_left: "请遮住左眼", vt_cover_right: "请遮住右眼",
    vt_acuity: "视力", vt_contrast: "对比敏感度",
    vt_acuity_desc: "选择E的朝向，字符会越来越小。",
    vt_contrast_desc: "E会越来越淡。在还能看见时选择朝向。",
    vt_begin: "准备好了", vt_which_dir: "E朝向哪个方向？",
    vt_result_title: "功能检查结果", vt_redo: "重新检查",
    vt_need_calib: "请先完成屏幕校准。",
    vt_asym: "⚠️ 双眼差异较大 — 可能为单眼病变，建议眼科检查。",
    q_age: "请问您的年龄段？", q_diabetes: "您有糖尿病吗？",
    q_hypertension: "您有高血压吗？", q_family: "家人中有被诊断为青光眼或黄斑变性的吗？",
    q_smoking: "您目前吸烟吗？",
    age_under40: "40岁以下", age_40s: "40–49岁", age_50s: "50–59岁", age_60s: "60–69岁", age_70plus: "70岁以上",
    risk_diabetes: "糖尿病", risk_hypertension: "高血压", risk_family: "家族史", risk_smoking: "吸烟",
    tri_title: "建议措施", tri_now: "建议尽快就诊眼科",
    tri_weeks: "建议数周内进行眼科检查", tri_monitor: "通过定期检查观察",
    tri_now_why: "同时发现了值得关注的结果和危险因素。",
    tri_weeks_why: "发现了临界结果或危险因素。",
    tri_monitor_why: "目前没有特别的警示信号。",
    ams_which_left: "左眼检查 — 遮住右眼并注视中心点",
    ams_which_right: "右眼检查 — 遮住左眼并注视中心点",
    ams_result_both: "双眼正常", ams_result_left: "左眼异常", ams_result_right: "右眼异常", ams_result_bad: "双眼异常",
    consent_title: "保存结果的同意", consent_agree: "同意并保存", consent_skip: "不保存",
    consent_text: "检查结果与AI参考信息将保存到服务器。健康信息属于敏感信息，仅在您同意时保存，照片不会被保存。",
    rep_info_title: "AI参考信息", info_writing: "AI正在整理参考信息"
  }
};

// 병합 — 누락 언어가 있으면 콘솔로 즉시 드러난다
for (const lang of Object.keys(translations)) {
  if (!extraStrings[lang]) { console.error('[i18n] 확장 문자열 누락:', lang); continue; }
  Object.assign(translations[lang], extraStrings[lang]);
}

// 위험도 층화 문진 — 기존 증상 질문(녹내장·당뇨망막병증) 앞에 붙는다.
// 나이·기저질환은 증상 질문보다 예측력이 크면서 비용이 거의 없다.
const riskQuestions = [
  { code: 'age', key: 'q_age', type: 'choice',
    options: [
      { v: 'under40', key: 'age_under40', score: 0 },
      { v: '40s',     key: 'age_40s',     score: 1 },
      { v: '50s',     key: 'age_50s',     score: 2 },
      { v: '60s',     key: 'age_60s',     score: 3 },
      { v: '70plus',  key: 'age_70plus',  score: 4 },
    ] },
  { code: 'diabetes',     key: 'q_diabetes',     type: 'yesno', score: 3, labelKey: 'risk_diabetes' },
  { code: 'hypertension', key: 'q_hypertension', type: 'yesno', score: 1, labelKey: 'risk_hypertension' },
  { code: 'family',       key: 'q_family',       type: 'yesno', score: 2, labelKey: 'risk_family' },
  { code: 'smoking',      key: 'q_smoking',      type: 'yesno', score: 2, labelKey: 'risk_smoking' },
];

// 카드 방향 안내 — 폰은 카드를 세워야 폭 54mm·높이 85.6mm가 모두 화면에 들어간다.
Object.assign(translations.ko, {
  vt_orient_portrait: "카드를 <b>세로로 세워</b> 화면에 대고, 파란 사각형을 카드와 똑같이 맞추세요.",
  vt_orient_landscape: "카드를 <b>가로로 눕혀</b> 화면에 대고, 파란 사각형을 카드와 똑같이 맞추세요."
});
Object.assign(translations.en, {
  vt_orient_portrait: "Hold the card <b>upright (portrait)</b> against the screen and match the blue rectangle to it.",
  vt_orient_landscape: "Lay the card <b>sideways (landscape)</b> against the screen and match the blue rectangle to it."
});
Object.assign(translations.es, {
  vt_orient_portrait: "Coloque la tarjeta <b>en vertical</b> sobre la pantalla y ajuste el rectángulo azul a ella.",
  vt_orient_landscape: "Coloque la tarjeta <b>en horizontal</b> sobre la pantalla y ajuste el rectángulo azul a ella."
});
Object.assign(translations.fr, {
  vt_orient_portrait: "Placez la carte <b>à la verticale</b> sur l'écran et ajustez le rectangle bleu à sa taille.",
  vt_orient_landscape: "Placez la carte <b>à l'horizontale</b> sur l'écran et ajustez le rectangle bleu à sa taille."
});
Object.assign(translations.ja, {
  vt_orient_portrait: "カードを<b>縦向き</b>に画面へ当て、青い四角をカードにぴったり合わせてください。",
  vt_orient_landscape: "カードを<b>横向き</b>に画面へ当て、青い四角をカードにぴったり合わせてください。"
});
Object.assign(translations.zh, {
  vt_orient_portrait: "将卡片<b>竖放</b>贴在屏幕上，把蓝色矩形调整到与卡片一致。",
  vt_orient_landscape: "将卡片<b>横放</b>贴在屏幕上，把蓝色矩形调整到与卡片一致。"
});

// 카드를 화면에 대면 그 접촉이 터치로 인식돼 화면이 확대/스크롤되는 문제 안내
Object.assign(translations.ko, {
  vt_touch_hint: "카드를 화면 <b>위쪽 가장자리</b>에 걸쳐 대고, 아래 <b>+/−</b> 버튼으로 크기를 맞추세요. 이 단계에서는 화면 확대·스크롤이 잠시 꺼집니다.",
  vt_nudge_fine: "미세", vt_nudge_coarse: "크게"
});
Object.assign(translations.en, {
  vt_touch_hint: "Rest the card along the <b>top edge</b> of the screen and use the <b>+/−</b> buttons below to size it. Pinch-zoom and scrolling are turned off during this step.",
  vt_nudge_fine: "Fine", vt_nudge_coarse: "Coarse"
});
Object.assign(translations.es, {
  vt_touch_hint: "Apoye la tarjeta en el <b>borde superior</b> de la pantalla y use los botones <b>+/−</b> para ajustar. El zoom y el desplazamiento se desactivan en este paso.",
  vt_nudge_fine: "Fino", vt_nudge_coarse: "Grueso"
});
Object.assign(translations.fr, {
  vt_touch_hint: "Posez la carte le long du <b>bord supérieur</b> de l'écran et utilisez les boutons <b>+/−</b> pour ajuster. Le zoom et le défilement sont désactivés à cette étape.",
  vt_nudge_fine: "Fin", vt_nudge_coarse: "Large"
});
Object.assign(translations.ja, {
  vt_touch_hint: "カードを画面の<b>上端</b>に沿えて置き、下の<b>+/−</b>ボタンでサイズを合わせてください。この手順では拡大・スクロールを一時的に無効化します。",
  vt_nudge_fine: "微調整", vt_nudge_coarse: "粗調整"
});
Object.assign(translations.zh, {
  vt_touch_hint: "把卡片贴在屏幕<b>上边缘</b>，用下方的<b>+/−</b>按钮调整大小。此步骤会暂时关闭缩放与滚动。",
  vt_nudge_fine: "微调", vt_nudge_coarse: "粗调"
});

// 화면 고정 토글 + 거리 측정 안내
Object.assign(translations.ko, {
  vt_lock_off: "🔓 화면 고정하기", vt_lock_on: "🔒 고정됨 — 해제하려면 탭",
  vt_lock_hint: "카드를 올려놓을 위치까지 스크롤한 뒤 <b>화면 고정</b>을 누르세요. 고정하면 카드가 닿아도 화면이 움직이지 않고, <b>+/−</b> 버튼으로만 크기를 바꿉니다.",
  vt_dist_tolerance: "거리가 10% 틀려도 시력 오차는 0.04 logMAR — <b>시력표 반 줄도 안 됩니다</b>. 대비감도는 이보다도 둔감하고, 좌우 눈 비교는 거리와 아예 무관합니다.",
  vt_dist_custom: "직접 입력 (cm)"
});
Object.assign(translations.en, {
  vt_lock_off: "🔓 Lock the screen", vt_lock_on: "🔒 Locked — tap to unlock",
  vt_lock_hint: "Scroll to where you want to rest the card, then tap <b>Lock the screen</b>. While locked, the card touching the screen won't move it — resize with the <b>+/−</b> buttons only.",
  vt_dist_tolerance: "A 10% distance error shifts acuity by only 0.04 logMAR — <b>less than half a line</b> on an eye chart. Contrast sensitivity is even less sensitive, and left/right comparison doesn't depend on distance at all.",
  vt_dist_custom: "Enter manually (cm)"
});
Object.assign(translations.es, {
  vt_lock_off: "🔓 Bloquear pantalla", vt_lock_on: "🔒 Bloqueada — toque para desbloquear",
  vt_lock_hint: "Desplácese hasta donde apoyará la tarjeta y pulse <b>Bloquear pantalla</b>. Bloqueada, la tarjeta no moverá la pantalla; ajuste solo con <b>+/−</b>.",
  vt_dist_tolerance: "Un error del 10% en distancia cambia la agudeza solo 0,04 logMAR — <b>menos de media línea</b>. La sensibilidad al contraste es aún menos sensible.",
  vt_dist_custom: "Introducir (cm)"
});
Object.assign(translations.fr, {
  vt_lock_off: "🔓 Verrouiller l'écran", vt_lock_on: "🔒 Verrouillé — touchez pour déverrouiller",
  vt_lock_hint: "Faites défiler jusqu'à l'endroit où poser la carte, puis touchez <b>Verrouiller l'écran</b>. Une fois verrouillé, la carte ne fera plus bouger l'écran ; ajustez avec <b>+/−</b>.",
  vt_dist_tolerance: "Une erreur de 10% sur la distance ne décale l'acuité que de 0,04 logMAR — <b>moins d'une demi-ligne</b>. La sensibilité au contraste y est encore moins sensible.",
  vt_dist_custom: "Saisir (cm)"
});
Object.assign(translations.ja, {
  vt_lock_off: "🔓 画面を固定", vt_lock_on: "🔒 固定中 — タップで解除",
  vt_lock_hint: "カードを置きたい位置までスクロールしてから<b>画面を固定</b>を押してください。固定中はカードが触れても画面が動かず、<b>+/−</b>ボタンだけでサイズを変えます。",
  vt_dist_tolerance: "距離が10%ずれても視力の誤差は0.04 logMAR — <b>視力表の半行未満</b>です。コントラスト感度はさらに鈍感で、左右比較は距離と無関係です。",
  vt_dist_custom: "直接入力 (cm)"
});
Object.assign(translations.zh, {
  vt_lock_off: "🔓 锁定屏幕", vt_lock_on: "🔒 已锁定 — 点击解锁",
  vt_lock_hint: "先滚动到想放卡片的位置，再点<b>锁定屏幕</b>。锁定后卡片接触屏幕也不会移动画面，只用<b>+/−</b>按钮调整大小。",
  vt_dist_tolerance: "距离偏差10%时视力误差仅0.04 logMAR — <b>不到视力表半行</b>。对比敏感度更不敏感，左右眼比较则与距离无关。",
  vt_dist_custom: "手动输入 (cm)"
});

// ==========================================================================
// 질환별 문진 재설계
//
// 기존: 녹내장·당뇨망막병증에 각각 "증상 있나요?" 1문항씩.
//   녹내장은 말기까지 자각 증상이 거의 없어서 "시야가 좁아진 느낌"에 '예'라고
//   답할 수 있는 사람은 이미 늦은 단계다. 즉 조기발견 목적의 스크리닝으로는 성립하지 않는다.
//   당뇨망막병증도 마찬가지로 비문증은 비특이적이다.
//
// 재설계 원칙:
//   1) 증상이 없는 질환은 '과거력 · 위험인자 · 검진 공백'을 묻는다.
//      (안압 지적받은 적, 고도근시, 마지막 안저검사 시기 등)
//   2) 증상이 실제로 유용한 질환(백내장)은 증상군으로 세분한다.
//   3) 응급 신호는 따로 맨 앞에서 잡는다 — 급성 폐쇄각 녹내장과 갑작스러운 시력상실은
//      몇 시간이 시력을 가르므로 '수 주 내 검진'으로 안내하면 안 된다.
//   4) 조건부 분기: 당뇨망막병증 문항은 당뇨가 있다고 답한 사람에게만 묻는다.
//      (비당뇨에게 묻는 것은 시간 낭비이자 결과 왜곡)
//
// invert:true 는 '아니오'가 위험 신호라는 뜻(예: 최근 검진을 받지 않음).
// ==========================================================================
const symptomQuestions = [
  // ── 응급 신호 (가장 먼저) ─────────────────────────────
  { code: 'rf_acute',  key: 'q_rf_acute',  disease: 'glaucoma',    weight: 0, redFlag: true },
  { code: 'rf_sudden', key: 'q_rf_sudden', disease: 'general',     weight: 0, redFlag: true },

  // ── 백내장: 증상이 실제로 유용한 질환 ──────────────────
  { code: 'cat_glare',   key: 'q_cat_glare',   disease: 'cataract', weight: 2 },
  { code: 'cat_foggy',   key: 'q_cat_foggy',   disease: 'cataract', weight: 2 },
  { code: 'cat_glasses', key: 'q_cat_glasses', disease: 'cataract', weight: 1 },

  // ── 황반변성: 왜곡은 암슬러가 담당, 여기선 중심암점 ────
  { code: 'amd_center', key: 'q_amd_center', disease: 'macular', weight: 2 },

  // ── 녹내장: 초기 무증상 → 과거력·위험인자 중심 ─────────
  { code: 'gla_iop',    key: 'q_gla_iop',    disease: 'glaucoma', weight: 3 },
  { code: 'gla_myopia', key: 'q_gla_myopia', disease: 'glaucoma', weight: 2 },
  { code: 'gla_field',  key: 'q_gla_field',  disease: 'glaucoma', weight: 2 },

  // ── 당뇨망막병증: 당뇨가 있을 때만 묻는다 ──────────────
  { code: 'dr_duration', key: 'q_dr_duration', disease: 'retinopathy', weight: 3, showIf: 'diabetes' },
  { code: 'dr_fundus',   key: 'q_dr_fundus',   disease: 'retinopathy', weight: 2, showIf: 'diabetes', invert: true },
  { code: 'dr_floaters', key: 'q_dr_floaters', disease: 'retinopathy', weight: 2, showIf: 'diabetes' },

  // ── 공통: 검진 공백 ────────────────────────────────────
  { code: 'chk_recent', key: 'q_chk_recent', disease: 'general', weight: 2, invert: true },
];

Object.assign(translations.ko, {
  q_rf_sudden: "갑자기(몇 시간~며칠 사이) 한쪽 눈이 잘 안 보이게 된 적이 있나요?",
  q_cat_glare: "밤에 운전하거나 불빛을 볼 때 빛이 심하게 번지거나 눈이 부신가요?",
  q_cat_foggy: "안개가 낀 것처럼 전체적으로 뿌옇게 보이나요?",
  q_cat_glasses: "최근 몇 년 사이 안경이나 돋보기 도수를 자주 바꾸셨나요?",
  q_amd_center: "글자를 읽을 때 가운데 글자가 빠져 보이거나 유독 흐린가요?",
  q_gla_field: "옆에서 오는 사람이나 물체를 자주 못 보고 부딪히나요?",
  q_dr_duration: "당뇨를 앓으신 지 10년이 넘었나요?",
  q_chk_recent: "최근 2년 안에 안과 검진을 받으신 적이 있나요?",
  sym_cat_glare: "빛 번짐·눈부심", sym_cat_foggy: "뿌옇게 보임", sym_cat_glasses: "도수 잦은 변경",
  sym_amd_center: "중심 시야 이상", sym_gla_iop: "안압 상승 지적", sym_gla_myopia: "고도근시",
  sym_gla_field: "주변 시야 이상", sym_dr_duration: "당뇨 10년 이상", sym_dr_fundus: "안저검사 미시행",
  sym_dr_floaters: "비문증 급증", sym_chk_recent: "2년 내 검진 없음",
  sym_rf_acute: "급성 안통·무지개 테", sym_rf_sudden: "갑작스러운 시력저하",
  tri_urgent: "지금 바로 안과 진료를 받으세요",
  tri_urgent_why: "응급 처치가 필요할 수 있는 신호입니다. 급성 녹내장이나 망막 이상은 몇 시간이 시력을 좌우합니다. 야간·주말이면 응급실로 가세요.",
  survey_progress: "{c} / {n}"
});
Object.assign(translations.en, {
  q_rf_sudden: "Have you suddenly (within hours or days) lost vision in one eye?",
  q_cat_glare: "Do lights glare or streak badly, especially when driving at night?",
  q_cat_foggy: "Does your vision look generally hazy, as if through fog?",
  q_cat_glasses: "Have you changed your glasses or reading prescription often in the last few years?",
  q_amd_center: "When reading, do letters in the middle look missing or unusually blurred?",
  q_gla_field: "Do you often miss or bump into people and objects approaching from the side?",
  q_dr_duration: "Have you had diabetes for more than 10 years?",
  q_chk_recent: "Have you had an eye exam within the last 2 years?",
  sym_cat_glare: "Glare / light streaking", sym_cat_foggy: "Hazy vision", sym_cat_glasses: "Frequent prescription changes",
  sym_amd_center: "Central vision problem", sym_gla_iop: "High eye pressure noted", sym_gla_myopia: "High myopia",
  sym_gla_field: "Peripheral vision problem", sym_dr_duration: "Diabetes over 10 years", sym_dr_fundus: "No recent fundus exam",
  sym_dr_floaters: "Sudden increase in floaters", sym_chk_recent: "No exam in 2 years",
  sym_rf_acute: "Acute eye pain with halos", sym_rf_sudden: "Sudden vision loss",
  tri_urgent: "Seek eye care right now",
  tri_urgent_why: "These signs may need emergency treatment. With acute glaucoma or retinal problems, hours can decide the outcome. Go to an emergency department if it is night or the weekend.",
  survey_progress: "{c} / {n}"
});
Object.assign(translations.es, {
  q_rf_sudden: "¿Ha perdido la visión de un ojo de forma repentina (en horas o días)?",
  q_cat_glare: "¿Las luces le deslumbran o se dispersan mucho, sobre todo al conducir de noche?",
  q_cat_foggy: "¿Ve todo borroso como a través de niebla?",
  q_cat_glasses: "¿Ha cambiado de graduación con frecuencia en los últimos años?",
  q_amd_center: "Al leer, ¿faltan letras en el centro o se ven especialmente borrosas?",
  q_gla_field: "¿Choca a menudo con personas u objetos que vienen de lado?",
  q_dr_duration: "¿Tiene diabetes desde hace más de 10 años?",
  q_chk_recent: "¿Se ha hecho una revisión ocular en los últimos 2 años?",
  sym_cat_glare: "Deslumbramiento", sym_cat_foggy: "Visión brumosa", sym_cat_glasses: "Cambios frecuentes de graduación",
  sym_amd_center: "Problema de visión central", sym_gla_iop: "Presión ocular alta", sym_gla_myopia: "Miopía alta",
  sym_gla_field: "Problema de visión periférica", sym_dr_duration: "Diabetes +10 años", sym_dr_fundus: "Sin fondo de ojo reciente",
  sym_dr_floaters: "Aumento de moscas volantes", sym_chk_recent: "Sin revisión en 2 años",
  sym_rf_acute: "Dolor ocular agudo con halos", sym_rf_sudden: "Pérdida súbita de visión",
  tri_urgent: "Acuda a un oftalmólogo ahora mismo",
  tri_urgent_why: "Estos signos pueden requerir tratamiento urgente. En el glaucoma agudo o problemas de retina, las horas cuentan. Vaya a urgencias si es de noche o fin de semana.",
  survey_progress: "{c} / {n}"
});
Object.assign(translations.fr, {
  q_rf_sudden: "Avez-vous perdu la vue d'un œil brutalement (en quelques heures ou jours) ?",
  q_cat_glare: "Les lumières vous éblouissent-elles fortement, surtout en conduisant la nuit ?",
  q_cat_foggy: "Votre vision est-elle globalement voilée, comme dans le brouillard ?",
  q_cat_glasses: "Avez-vous changé souvent de correction ces dernières années ?",
  q_amd_center: "En lisant, des lettres manquent-elles au centre ou sont-elles très floues ?",
  q_gla_field: "Heurtez-vous souvent des personnes ou objets venant de côté ?",
  q_dr_duration: "Êtes-vous diabétique depuis plus de 10 ans ?",
  q_chk_recent: "Avez-vous consulté un ophtalmologiste ces 2 dernières années ?",
  sym_cat_glare: "Éblouissement", sym_cat_foggy: "Vision voilée", sym_cat_glasses: "Changements fréquents de correction",
  sym_amd_center: "Trouble de la vision centrale", sym_gla_iop: "Tension oculaire élevée", sym_gla_myopia: "Forte myopie",
  sym_gla_field: "Trouble du champ périphérique", sym_dr_duration: "Diabète +10 ans", sym_dr_fundus: "Pas de fond d'œil récent",
  sym_dr_floaters: "Corps flottants en hausse", sym_chk_recent: "Aucun examen en 2 ans",
  sym_rf_acute: "Douleur aiguë avec halos", sym_rf_sudden: "Perte de vue brutale",
  tri_urgent: "Consultez un ophtalmologiste immédiatement",
  tri_urgent_why: "Ces signes peuvent nécessiter un traitement urgent. En cas de glaucome aigu ou d'atteinte rétinienne, quelques heures comptent. Allez aux urgences la nuit ou le week-end.",
  survey_progress: "{c} / {n}"
});
Object.assign(translations.ja, {
  q_rf_sudden: "急に（数時間〜数日で）片目が見えにくくなったことがありますか？",
  q_cat_glare: "夜の運転や光を見たとき、光がひどくにじんだり眩しかったりしますか？",
  q_cat_foggy: "霧がかかったように全体的にかすんで見えますか？",
  q_cat_glasses: "ここ数年、眼鏡や老眼鏡の度数を頻繁に変えましたか？",
  q_amd_center: "文字を読むとき、中央の文字が欠けたり特にぼやけたりしますか？",
  q_gla_field: "横から来る人や物によくぶつかりますか？",
  q_dr_duration: "糖尿病になって10年以上経ちますか？",
  q_chk_recent: "この2年以内に眼科検診を受けましたか？",
  sym_cat_glare: "光のにじみ・眩しさ", sym_cat_foggy: "かすみ目", sym_cat_glasses: "度数の頻繁な変更",
  sym_amd_center: "中心視野の異常", sym_gla_iop: "眼圧上昇の指摘", sym_gla_myopia: "強度近視",
  sym_gla_field: "周辺視野の異常", sym_dr_duration: "糖尿病10年以上", sym_dr_fundus: "眼底検査未実施",
  sym_dr_floaters: "飛蚊症の急増", sym_chk_recent: "2年以内の検診なし",
  sym_rf_acute: "急性の眼痛・虹輪視", sym_rf_sudden: "急激な視力低下",
  tri_urgent: "今すぐ眼科を受診してください",
  tri_urgent_why: "緊急処置が必要な可能性のある兆候です。急性緑内障や網膜の異常は数時間が視力を左右します。夜間・週末なら救急外来へ。",
  survey_progress: "{c} / {n}"
});
Object.assign(translations.zh, {
  q_rf_sudden: "是否曾在数小时到数天内突然出现单眼视力下降？",
  q_cat_glare: "夜间开车或看灯光时，是否有明显的光晕或刺眼感？",
  q_cat_foggy: "视野是否像蒙上一层雾一样整体发白模糊？",
  q_cat_glasses: "近几年是否频繁更换眼镜或老花镜度数？",
  q_amd_center: "阅读时中间的字是否缺失或特别模糊？",
  q_gla_field: "是否经常撞到从侧面来的人或物？",
  q_dr_duration: "您患糖尿病是否已超过10年？",
  q_chk_recent: "最近两年内是否做过眼科检查？",
  sym_cat_glare: "光晕·眩光", sym_cat_foggy: "视物模糊发雾", sym_cat_glasses: "频繁换度数",
  sym_amd_center: "中心视野异常", sym_gla_iop: "眼压偏高", sym_gla_myopia: "高度近视",
  sym_gla_field: "周边视野异常", sym_dr_duration: "糖尿病10年以上", sym_dr_fundus: "未做眼底检查",
  sym_dr_floaters: "飞蚊突然增多", sym_chk_recent: "两年内无检查",
  sym_rf_acute: "急性眼痛伴虹视", sym_rf_sudden: "突发视力下降",
  tri_urgent: "请立即就诊眼科",
  tri_urgent_why: "这些信号可能需要急诊处理。急性青光眼或视网膜病变，数小时就可能决定视力结局。夜间或周末请前往急诊。",
  survey_progress: "{c} / {n}"
});

// ==========================================================================
// (1) 전문 용어에 짧은 설명 덧붙이기
//     용어 자체는 유지한다 — 사용자가 안과에서 그 말을 들었을 때 알아들어야 하므로.
//     대신 괄호로 "그게 뭔지"를 붙여 지금 답할 수 있게 한다.
// (2) 보는 거리: 준비물 없는 '팔 뻗은 거리'를 기본값으로
//     A4를 찾아와야 한다면 '간편한 자가검사'라는 전제가 깨진다.
//     거리 10% 오차 = 시력 0.04 logMAR(시력표 반 줄 미만)이므로 팔 길이로 충분하다.
//     정밀하게 재고 싶은 사람을 위해 A4·카드 방법은 '선택'으로 남긴다.
// ==========================================================================
Object.assign(translations.ko, {
  q_gla_iop: "안과에서 '안압이 높다'는 말을 들은 적이 있나요? (안압 = 눈 속의 압력. 건강검진 안과 항목에서도 잽니다)",
  q_gla_myopia: "고도근시인가요? (안경 도수 -6.00 이상. 안경을 벗으면 팔 뻗은 거리의 손가락도 흐릿한 정도예요)",
  q_dr_fundus: "최근 1년 안에 안저 검사를 받으셨나요? (안저 = 눈 안쪽 망막. 눈에 약을 넣어 동공을 키우고 들여다보는 검사입니다)",
  q_dr_floaters: "눈앞에 검은 점이나 실오라기 같은 것(비문증)이 갑자기 많아졌나요?",
  q_rf_acute: "최근 눈이 심하게 아프면서 두통·구역질이 나고, 불빛 주위에 무지개 같은 테가 보인 적이 있나요?",
  vt_dist_label: "화면에서 눈까지 거리",
  dist_arm: "팔 뻗은 거리 (약 60cm) · 준비물 없음",
  vt_dist_how: "더 정확히 재고 싶다면 (선택)",
  vt_dist_guide: "<b>그냥 팔을 쭉 뻗은 거리면 충분합니다.</b> 준비물이 필요 없고, 아래 설명처럼 오차가 결과를 크게 바꾸지 않아요.<br><br>더 정확히 재고 싶다면, 캘리브레이션에 쓴 <b>카드 긴 변이 8.56cm</b>이고 <b>A4 긴 변이 29.7cm</b>입니다.<br>· <b>60cm</b> = A4 긴 변 <b>2번</b> (59.4cm)<br>· <b>40cm</b> = A4 긴 변 <b>1번</b> + 카드 <b>1.2번</b>",
  vt_dist_tolerance: "거리가 10% 틀려도 시력 오차는 0.04 logMAR — <b>시력표 반 줄도 안 됩니다</b>. 대비감도는 이보다 더 둔감하고, <b>이 앱에서 가장 신뢰도 높은 지표인 좌우 눈 비교는 거리와 아예 무관합니다</b>."
});
Object.assign(translations.en, {
  q_gla_iop: "Has an eye doctor ever told you your eye pressure was high? (Eye pressure = the fluid pressure inside your eye, measured at routine eye exams)",
  q_gla_myopia: "Are you highly myopic? (Glasses stronger than -6.00 — without them, even your fingers at arm's length look blurry)",
  q_dr_fundus: "Have you had a fundus exam within the last year? (Fundus = the retina at the back of the eye; drops widen the pupil so the doctor can look inside)",
  q_dr_floaters: "Has the number of dark spots or thread-like floaters in your vision suddenly increased?",
  q_rf_acute: "Have you recently had severe eye pain with headache or nausea, and seen rainbow-like rings around lights?",
  vt_dist_label: "Distance from screen to your eyes",
  dist_arm: "Arm's length (about 60cm) · nothing needed",
  vt_dist_how: "Want to measure it more precisely? (optional)",
  vt_dist_guide: "<b>Just holding it at arm's length is enough.</b> Nothing to fetch, and as explained below the error barely changes the result.<br><br>If you want more precision: the card you calibrated with is <b>8.56cm</b> on its long edge and A4 paper is <b>29.7cm</b>.<br>· <b>60cm</b> = A4 long edge <b>×2</b> (59.4cm)<br>· <b>40cm</b> = A4 <b>×1</b> + card <b>×1.2</b>",
  vt_dist_tolerance: "A 10% distance error shifts acuity by only 0.04 logMAR — <b>less than half a line</b> on an eye chart. Contrast sensitivity is even less sensitive, and <b>the left/right comparison — this app's most reliable signal — doesn't depend on distance at all</b>."
});
Object.assign(translations.es, {
  q_gla_iop: "¿Le han dicho que tiene la presión ocular alta? (Presión ocular = la presión del líquido dentro del ojo, se mide en revisiones)",
  q_gla_myopia: "¿Tiene miopía alta? (Graduación superior a -6,00 — sin gafas, ni los dedos con el brazo extendido se ven nítidos)",
  q_dr_fundus: "¿Se ha hecho un examen de fondo de ojo en el último año? (Fondo de ojo = la retina; con gotas se dilata la pupila para mirar dentro)",
  q_dr_floaters: "¿Han aumentado de golpe los puntos oscuros o filamentos (moscas volantes)?",
  q_rf_acute: "¿Ha tenido dolor ocular intenso con dolor de cabeza o náuseas, y halos como un arcoíris alrededor de las luces?",
  vt_dist_label: "Distancia de la pantalla a sus ojos",
  dist_arm: "Con el brazo extendido (unos 60cm) · sin preparativos",
  vt_dist_how: "¿Quiere medirlo con más precisión? (opcional)",
  vt_dist_guide: "<b>Con el brazo extendido basta.</b> No hace falta nada más y, como se explica abajo, el error apenas cambia el resultado.<br><br>Si quiere más precisión: la tarjeta mide <b>8,56cm</b> de lado largo y un A4 <b>29,7cm</b>.<br>· <b>60cm</b> = A4 <b>×2</b> (59,4cm)<br>· <b>40cm</b> = A4 <b>×1</b> + tarjeta <b>×1,2</b>",
  vt_dist_tolerance: "Un error del 10% cambia la agudeza solo 0,04 logMAR — <b>menos de media línea</b>. La sensibilidad al contraste es aún menos sensible, y <b>la comparación entre ojos, la señal más fiable de esta app, no depende de la distancia</b>."
});
Object.assign(translations.fr, {
  q_gla_iop: "Un ophtalmologiste vous a-t-il dit que votre tension oculaire était élevée ? (Tension oculaire = la pression du liquide dans l'œil, mesurée lors des examens)",
  q_gla_myopia: "Êtes-vous fortement myope ? (Correction au-delà de -6,00 — sans lunettes, même vos doigts à bout de bras sont flous)",
  q_dr_fundus: "Avez-vous eu un examen du fond d'œil cette dernière année ? (Fond d'œil = la rétine ; des gouttes dilatent la pupille pour regarder à l'intérieur)",
  q_dr_floaters: "Le nombre de points noirs ou filaments (corps flottants) a-t-il augmenté brusquement ?",
  q_rf_acute: "Avez-vous eu une douleur oculaire intense avec maux de tête ou nausées, et des halos comme un arc-en-ciel autour des lumières ?",
  vt_dist_label: "Distance entre l'écran et vos yeux",
  dist_arm: "À bout de bras (environ 60cm) · rien à préparer",
  vt_dist_how: "Mesurer plus précisément ? (facultatif)",
  vt_dist_guide: "<b>À bout de bras, cela suffit.</b> Rien à aller chercher, et comme expliqué ci-dessous l'erreur ne change presque rien.<br><br>Pour plus de précision : la carte fait <b>8,56cm</b> de grand côté et un A4 <b>29,7cm</b>.<br>· <b>60cm</b> = A4 <b>×2</b> (59,4cm)<br>· <b>40cm</b> = A4 <b>×1</b> + carte <b>×1,2</b>",
  vt_dist_tolerance: "Une erreur de 10% ne décale l'acuité que de 0,04 logMAR — <b>moins d'une demi-ligne</b>. La sensibilité au contraste y est encore moins sensible, et <b>la comparaison entre les deux yeux, le signal le plus fiable de cette app, ne dépend pas de la distance</b>."
});
Object.assign(translations.ja, {
  q_gla_iop: "眼科で「眼圧が高い」と言われたことがありますか？（眼圧＝目の中の圧力。健診の眼科項目でも測ります）",
  q_gla_myopia: "強度近視ですか？（度数 -6.00 以上。眼鏡を外すと腕を伸ばした先の指もぼやける程度です）",
  q_dr_fundus: "この1年以内に眼底検査を受けましたか？（眼底＝目の奥の網膜。目薬で瞳孔を広げて中を見る検査です）",
  q_dr_floaters: "黒い点や糸くずのようなもの（飛蚊症）が急に増えましたか？",
  q_rf_acute: "最近、強い目の痛みと頭痛・吐き気があり、光の周りに虹のような輪が見えたことはありますか？",
  vt_dist_label: "画面から目までの距離",
  dist_arm: "腕を伸ばした距離（約60cm）・準備物なし",
  vt_dist_how: "もっと正確に測りたい場合（任意）",
  vt_dist_guide: "<b>腕を伸ばした距離で十分です。</b>準備物は要らず、下の説明のとおり誤差は結果をほとんど変えません。<br><br>より正確に測るなら、キャリブレーションに使ったカードの長辺が<b>8.56cm</b>、A4の長辺が<b>29.7cm</b>です。<br>· <b>60cm</b> = A4長辺<b>2回</b>(59.4cm)<br>· <b>40cm</b> = A4<b>1回</b> + カード<b>1.2回</b>",
  vt_dist_tolerance: "距離が10%ずれても視力の誤差は0.04 logMAR — <b>視力表の半行未満</b>です。コントラスト感度はさらに鈍感で、<b>このアプリで最も信頼できる指標である左右差は距離と無関係</b>です。"
});
Object.assign(translations.zh, {
  q_gla_iop: "眼科医生是否说过您的眼压偏高？（眼压＝眼球内部的压力，体检的眼科项目也会测）",
  q_gla_myopia: "您是高度近视吗？（度数超过 -6.00，不戴眼镜时连伸直手臂的手指都看不清）",
  q_dr_fundus: "最近一年内做过眼底检查吗？（眼底＝眼球后部的视网膜，需滴药水散瞳后查看）",
  q_dr_floaters: "眼前的黑点或丝状物（飞蚊症）是否突然增多？",
  q_rf_acute: "最近是否有剧烈眼痛伴头痛、恶心，并在灯光周围看到彩虹样的光圈？",
  vt_dist_label: "屏幕到眼睛的距离",
  dist_arm: "手臂伸直的距离（约60cm）· 无需准备",
  vt_dist_how: "想量得更准确？（可选）",
  vt_dist_guide: "<b>手臂伸直的距离就够了。</b>无需任何准备，且如下所述误差几乎不改变结果。<br><br>若想更准确：校准用的卡片长边<b>8.56cm</b>，A4纸长边<b>29.7cm</b>。<br>· <b>60cm</b> = A4长边<b>×2</b>(59.4cm)<br>· <b>40cm</b> = A4<b>×1</b> + 卡片<b>×1.2</b>",
  vt_dist_tolerance: "距离偏差10%时视力误差仅0.04 logMAR — <b>不到视力表半行</b>。对比敏感度更不敏感，而<b>本应用最可靠的指标——左右眼比较——与距离完全无关</b>。"
});

// ==========================================================================
// 결정론적 검사 해석 + '확률' 표기 정정
//
// 왜: LLM에게 해석을 맡겼더니 "암슬러가 정상이므로 녹내장 가능성이 낮다"는 문장이
//     실제로 나왔다. 해석은 코드가 고정 문구로 만들고, LLM은 생활 조언만 담당한다.
//
// 왜 '확률'이 아니라 '위험 점수': 모델 출력은 보정(calibration)되지 않은 softmax 값이다.
//     Brier/ECE/temperature scaling 어느 것도 적용하지 않았으므로 "백내장일 확률 87%"로
//     읽히면 안 된다. 표기를 바꾸고, 문구로도 확률이 아님을 명시한다.
// ==========================================================================
Object.assign(translations.ko, {
  score_label: "AI 위험 점수",
  score_note: "이 숫자는 질병에 걸릴 확률이 아니라, AI가 사진에서 백내장 특징을 얼마나 강하게 감지했는지를 나타내는 점수입니다.",
  find_title: "검사 요약 해석",
  find_cat_risk: "백내장 AI가 수정체 혼탁으로 보이는 특징을 강하게 감지했습니다. 확진은 안과의 세극등 현미경 검사로만 가능합니다.",
  find_cat_borderline: "백내장 AI 점수가 경계 구간입니다. 촬영 조건 때문일 수도 있어 재촬영 또는 안과 확인을 권합니다.",
  find_cat_normal: "백내장 AI가 이번 사진에서 뚜렷한 혼탁 특징을 감지하지 않았습니다. 다만 초기 백내장은 겉사진에 나타나지 않을 수 있어, 이 결과로 백내장을 배제할 수는 없습니다.",
  find_cat_asym: "좌우 눈의 점수 차이가 큽니다. 한쪽 눈에만 변화가 진행됐을 수 있어 양안 비교 검진이 필요합니다.",
  find_ams_normal: "암슬러 격자 자가검사에서 좌우 모두 뚜렷한 왜곡·암점 응답이 없었습니다. 이 검사는 황반(중심시야)만 확인하므로, 다른 부위나 다른 질환은 평가하지 않습니다.",
  find_ams_abnormal: "암슬러 격자에서 이상 응답이 있었습니다({eye}). 황반(중심시야) 확인이 필요하며, 안저 검사나 OCT로 확인합니다.",
  find_sym: "문진에서 확인된 항목: {items}. 각 항목은 해당 질환의 위험을 높이는 요소이며, 그 자체로 질환을 뜻하지는 않습니다.",
  find_nosym: "문진에서 특별히 확인된 항목은 없었습니다.",
  find_disclaimer: "위 해석은 앱이 검사 결과에 따라 고정된 문장으로 생성한 것이며, 개별 상황을 판단한 것이 아닙니다.",
  gate_title: "먼저 검사를 완료해 주세요",
  gate_desc: "AI 검사 탭에서 사진 분석과 문진을 마치면 결과 리포트가 여기에 표시됩니다.",
  gate_go: "AI 검사 시작하기"
});
Object.assign(translations.en, {
  score_label: "AI risk score",
  score_note: "This number is not the probability of having the disease. It shows how strongly the AI detected cataract-like features in the photo.",
  find_title: "Result summary",
  find_cat_risk: "The cataract AI strongly detected features consistent with lens clouding. Only a slit-lamp exam at a clinic can confirm this.",
  find_cat_borderline: "The cataract AI score is in the borderline band. Photo conditions may explain it, so retaking the photo or an eye exam is recommended.",
  find_cat_normal: "The cataract AI did not detect clear clouding features in this photo. Early cataract may not be visible from the outside, so this result cannot rule cataract out.",
  find_cat_asym: "The two eyes scored quite differently. Change may be progressing in one eye only, so a comparative exam of both eyes is needed.",
  find_ams_normal: "The Amsler self-test showed no clear distortion or blind-spot response in either eye. This test only checks the macula (central vision); it does not assess other areas or other conditions.",
  find_ams_abnormal: "The Amsler grid showed an abnormal response ({eye}). The macula needs checking, typically with a fundus exam or OCT.",
  find_sym: "Flagged in the questionnaire: {items}. Each item raises the risk of the related condition but does not by itself mean you have it.",
  find_nosym: "Nothing in particular was flagged in the questionnaire.",
  find_disclaimer: "This summary is generated by the app from fixed sentences based on your results. It is not an individual clinical judgement.",
  gate_title: "Please complete a screening first",
  gate_desc: "Finish the photo analysis and questionnaire in the AI Analysis tab and your report will appear here.",
  gate_go: "Start the screening"
});
Object.assign(translations.es, {
  score_label: "Puntuación de riesgo IA",
  score_note: "Este número no es la probabilidad de tener la enfermedad. Indica con qué intensidad la IA detectó rasgos de catarata en la foto.",
  find_title: "Resumen de resultados",
  find_cat_risk: "La IA detectó con fuerza rasgos compatibles con opacidad del cristalino. Solo un examen con lámpara de hendidura puede confirmarlo.",
  find_cat_borderline: "La puntuación está en la banda límite. Puede deberse a las condiciones de la foto; se recomienda repetirla o acudir a revisión.",
  find_cat_normal: "La IA no detectó rasgos claros de opacidad en esta foto. Las cataratas iniciales pueden no verse desde fuera, así que este resultado no las descarta.",
  find_cat_asym: "Los dos ojos puntuaron de forma muy distinta. Puede haber cambios en un solo ojo; conviene un examen comparativo.",
  find_ams_normal: "La autoprueba de Amsler no mostró distorsión ni escotoma claros en ninguno de los ojos. Esta prueba solo evalúa la mácula (visión central).",
  find_ams_abnormal: "La rejilla de Amsler mostró una respuesta anormal ({eye}). Conviene revisar la mácula con fondo de ojo u OCT.",
  find_sym: "Marcado en el cuestionario: {items}. Cada elemento aumenta el riesgo, pero por sí solo no significa que tenga la enfermedad.",
  find_nosym: "No se marcó nada especial en el cuestionario.",
  find_disclaimer: "Este resumen lo genera la app con frases fijas según sus resultados; no es un juicio clínico individual.",
  gate_title: "Complete primero una revisión",
  gate_desc: "Termine el análisis de foto y el cuestionario en la pestaña de Análisis IA y su informe aparecerá aquí.",
  gate_go: "Comenzar la revisión"
});
Object.assign(translations.fr, {
  score_label: "Score de risque IA",
  score_note: "Ce nombre n'est pas la probabilité d'avoir la maladie. Il indique à quel point l'IA a détecté des signes de cataracte sur la photo.",
  find_title: "Résumé des résultats",
  find_cat_risk: "L'IA a fortement détecté des signes compatibles avec une opacification du cristallin. Seul un examen à la lampe à fente peut le confirmer.",
  find_cat_borderline: "Le score est dans la zone limite. Les conditions de prise de vue peuvent l'expliquer ; reprenez la photo ou consultez.",
  find_cat_normal: "L'IA n'a pas détecté de signes nets d'opacification sur cette photo. Une cataracte débutante peut ne pas être visible de l'extérieur ; ce résultat ne l'exclut donc pas.",
  find_cat_asym: "Les deux yeux ont des scores très différents. Une évolution peut toucher un seul œil ; un examen comparatif est nécessaire.",
  find_ams_normal: "L'auto-test d'Amsler n'a montré ni déformation ni scotome net des deux côtés. Ce test n'évalue que la macula (vision centrale).",
  find_ams_abnormal: "La grille d'Amsler a montré une réponse anormale ({eye}). La macula doit être vérifiée par fond d'œil ou OCT.",
  find_sym: "Éléments relevés au questionnaire : {items}. Chacun augmente le risque mais ne signifie pas à lui seul la maladie.",
  find_nosym: "Rien de particulier n'a été relevé au questionnaire.",
  find_disclaimer: "Ce résumé est généré par l'application à partir de phrases fixes selon vos résultats ; ce n'est pas un jugement clinique individuel.",
  gate_title: "Veuillez d'abord effectuer un dépistage",
  gate_desc: "Terminez l'analyse photo et le questionnaire dans l'onglet Analyse IA ; votre rapport apparaîtra ici.",
  gate_go: "Commencer le dépistage"
});
Object.assign(translations.ja, {
  score_label: "AIリスクスコア",
  score_note: "この数値は病気である確率ではありません。AIが写真から白内障らしい特徴をどれだけ強く検出したかを示す点数です。",
  find_title: "検査結果の要約",
  find_cat_risk: "白内障AIが水晶体の混濁に相当する特徴を強く検出しました。確定は眼科の細隙灯顕微鏡検査でのみ可能です。",
  find_cat_borderline: "白内障AIのスコアが境界域です。撮影条件による可能性もあるため、再撮影または眼科での確認をお勧めします。",
  find_cat_normal: "今回の写真では明らかな混濁の特徴は検出されませんでした。初期白内障は外観に現れないことがあるため、この結果で白内障を否定することはできません。",
  find_cat_asym: "左右のスコア差が大きいです。片眼だけ変化が進んでいる可能性があり、両眼の比較検査が必要です。",
  find_ams_normal: "アムスラー自己検査では左右とも明らかな歪み・暗点の回答はありませんでした。この検査は黄斑(中心視野)のみを確認します。",
  find_ams_abnormal: "アムスラー格子で異常な回答がありました({eye})。黄斑の確認が必要で、眼底検査やOCTで調べます。",
  find_sym: "問診で確認された項目: {items}。各項目は該当疾患のリスクを高める要素であり、それ自体が疾患を意味するものではありません。",
  find_nosym: "問診で特に確認された項目はありませんでした。",
  find_disclaimer: "この要約はアプリが検査結果に応じて固定文から生成したもので、個別の臨床判断ではありません。",
  gate_title: "まず検査を完了してください",
  gate_desc: "AI検査タブで写真解析と問診を終えると、結果レポートがここに表示されます。",
  gate_go: "検査を始める"
});
Object.assign(translations.zh, {
  score_label: "AI风险评分",
  score_note: "该数字不是患病概率，而是表示AI在照片中检测到白内障特征的强度评分。",
  find_title: "检查结果摘要",
  find_cat_risk: "白内障AI强烈检测到与晶状体混浊相符的特征。确诊只能通过眼科裂隙灯检查。",
  find_cat_borderline: "白内障AI评分处于临界区间。可能与拍摄条件有关，建议重拍或到眼科确认。",
  find_cat_normal: "本次照片未检测到明显的混浊特征。早期白内障可能在外观上看不出来，因此该结果不能排除白内障。",
  find_cat_asym: "双眼评分差异较大。可能只有一只眼在进展，需要双眼对比检查。",
  find_ams_normal: "阿姆斯勒自测中双眼均无明显变形或暗点。该检查仅评估黄斑（中心视野）。",
  find_ams_abnormal: "阿姆斯勒方格出现异常（{eye}）。需要检查黄斑，通常通过眼底检查或OCT。",
  find_sym: "问诊中标记的项目：{items}。每项都会提高相应疾病的风险，但本身并不代表患病。",
  find_nosym: "问诊中没有特别标记的项目。",
  find_disclaimer: "本摘要由应用根据结果以固定语句生成，并非个体临床判断。",
  gate_title: "请先完成检查",
  gate_desc: "在AI检查标签完成照片分析与问诊后，结果报告将显示在这里。",
  gate_go: "开始检查"
});

// 지도 타일을 못 받는 환경(발표장 오프라인 등) 안내 — 다른 기능은 정상 동작한다
Object.assign(translations.ko, { map_offline: "지도를 불러올 수 없습니다. 인터넷 연결을 확인해주세요. AI 검사·문진·리포트·PDF는 정상 동작합니다.", map_offline_short: "지도 오프라인" });
Object.assign(translations.en, { map_offline: "The map could not be loaded. Check your internet connection. The screening, questionnaire, report and PDF all still work.", map_offline_short: "Map offline" });
Object.assign(translations.es, { map_offline: "No se pudo cargar el mapa. Revise su conexión. El análisis, el cuestionario, el informe y el PDF siguen funcionando.", map_offline_short: "Mapa sin conexión" });
Object.assign(translations.fr, { map_offline: "La carte n'a pas pu être chargée. Vérifiez votre connexion. Le dépistage, le questionnaire, le rapport et le PDF fonctionnent toujours.", map_offline_short: "Carte hors ligne" });
Object.assign(translations.ja, { map_offline: "地図を読み込めませんでした。インターネット接続をご確認ください。AI検査・問診・レポート・PDFは正常に動作します。", map_offline_short: "地図オフライン" });
Object.assign(translations.zh, { map_offline: "无法加载地图。请检查网络连接。AI检查、问诊、报告和PDF均可正常使用。", map_offline_short: "地图离线" });

// ==========================================================================
// 외부 리뷰 2차 반영: 기능검사 문구 완화 + 저장 상태 + 위험요인 표현
//
// 왜 완화하는가: "영향을 받지 않는다", "일치합니다", "초기 백내장을 보완"은
//   검증되지 않은 단정이다. 좌우 비교가 상대적으로 안정적인 것은 맞지만
//   화면 축소·검사 순서·피로·눈 가림 실패·화면 밝기 같은 교란을 아직 통제하지 못했다.
//   측정값은 '참고용'으로만 제시하고, 임상 시력값처럼 보이지 않게 한다.
// ==========================================================================
Object.assign(translations.ko, {
  vt_intro_desc: "화면에 표시한 시표로 좌우 눈의 기능 차이를 참고용으로 살펴봅니다. 임상 시력값이나 질환 진단을 제공하지 않습니다.",
  vt_beta_note: "참고용 측정입니다. 기기·조명·거리에 따라 값이 달라질 수 있어, 절대값보다 좌우 차이를 보는 용도로 쓰세요.",
  find_vt_asym: "기능검사에서 좌우 눈의 결과 차이가 관찰됐습니다. 참고용 측정이지만, 차이가 지속되면 안과에서 확인해 보세요.",
  find_vt_ok: "기능검사에서 좌우 눈의 뚜렷한 차이는 관찰되지 않았습니다(참고용 측정).",
  find_vt_unmeasurable: "한쪽 눈은 가장 큰 시표도 판별하지 못했습니다. 측정 조건 문제일 수도 있으나, 좌우 차이가 클 가능성이 있어 안과 확인을 권합니다.",
  vt_cross_match: "📌 사진 분석에서도 좌우 차이 소견이 있었습니다(두 결과 모두 참고용입니다).",
  tri_factors: "정기 검진을 권하는 이유: {items}",
  save_saving: "저장 중...", save_done: "저장했습니다.",
  save_failed: "저장하지 못했습니다. 결과는 화면에서 계속 보실 수 있습니다.", save_retry: "다시 시도",
  calib_stale: "화면 설정이 바뀐 것 같습니다(회전·확대·창 크기). 정확한 측정을 위해 다시 보정해 주세요."
});
Object.assign(translations.en, {
  vt_intro_desc: "Uses on-screen optotypes to look at the difference between your two eyes, for reference only. It does not provide a clinical acuity value or a diagnosis.",
  vt_beta_note: "Reference measurement. Values vary with device, lighting and distance, so use it to compare your two eyes rather than as an absolute number.",
  find_vt_asym: "A difference between your eyes was observed in the functional test. This is a reference measurement, but if the difference persists, have it checked at a clinic.",
  find_vt_ok: "No marked difference between your eyes was observed in the functional test (reference measurement).",
  find_vt_unmeasurable: "One eye could not identify even the largest optotype. This may be a testing-condition issue, but the difference between your eyes may be large, so an eye exam is recommended.",
  vt_cross_match: "📌 The photo analysis also showed a side difference (both are reference findings).",
  tri_factors: "Why regular check-ups are recommended: {items}",
  save_saving: "Saving...", save_done: "Saved.",
  save_failed: "Could not save. Your results remain visible on screen.", save_retry: "Try again",
  calib_stale: "Your display settings seem to have changed (rotation, zoom, window size). Please calibrate again for an accurate measurement."
});
Object.assign(translations.es, {
  vt_intro_desc: "Usa optotipos en pantalla para observar la diferencia entre sus dos ojos, solo como referencia. No ofrece agudeza clínica ni diagnóstico.",
  vt_beta_note: "Medición de referencia. Los valores varían según dispositivo, luz y distancia; úselo para comparar ambos ojos, no como valor absoluto.",
  find_vt_asym: "Se observó una diferencia entre ojos en la prueba funcional. Es una medición de referencia, pero si persiste conviene revisarla.",
  find_vt_ok: "No se observó una diferencia marcada entre ojos (medición de referencia).",
  find_vt_unmeasurable: "Un ojo no identificó ni el optotipo más grande. Puede deberse a las condiciones, pero la diferencia podría ser grande; se recomienda examen.",
  vt_cross_match: "📌 El análisis de foto también mostró diferencia lateral (ambos son hallazgos de referencia).",
  tri_factors: "Por qué se recomiendan revisiones periódicas: {items}",
  save_saving: "Guardando...", save_done: "Guardado.",
  save_failed: "No se pudo guardar. Sus resultados siguen visibles en pantalla.", save_retry: "Reintentar",
  calib_stale: "Parece que cambió la configuración de pantalla (rotación, zoom, tamaño). Calibre de nuevo."
});
Object.assign(translations.fr, {
  vt_intro_desc: "Utilise des optotypes à l'écran pour observer l'écart entre vos deux yeux, à titre indicatif. Ne fournit ni acuité clinique ni diagnostic.",
  vt_beta_note: "Mesure indicative. Les valeurs varient selon l'appareil, l'éclairage et la distance ; utilisez-la pour comparer les deux yeux.",
  find_vt_asym: "Un écart entre les yeux a été observé au test fonctionnel. Mesure indicative, mais s'il persiste, faites-le vérifier.",
  find_vt_ok: "Aucun écart marqué entre les yeux n'a été observé (mesure indicative).",
  find_vt_unmeasurable: "Un œil n'a pas identifié même le plus grand optotype. Cela peut venir des conditions, mais l'écart pourrait être important ; un examen est recommandé.",
  vt_cross_match: "📌 L'analyse photo montrait aussi une différence latérale (les deux sont indicatifs).",
  tri_factors: "Pourquoi des contrôles réguliers sont recommandés : {items}",
  save_saving: "Enregistrement...", save_done: "Enregistré.",
  save_failed: "Enregistrement impossible. Vos résultats restent affichés.", save_retry: "Réessayer",
  calib_stale: "Vos réglages d'affichage semblent avoir changé (rotation, zoom, taille). Veuillez recalibrer."
});
Object.assign(translations.ja, {
  vt_intro_desc: "画面に表示した視標で左右の差を参考として確認します。臨床的な視力値や診断は提供しません。",
  vt_beta_note: "参考測定です。機器・照明・距離で値が変わるため、絶対値ではなく左右差を見る用途にお使いください。",
  find_vt_asym: "機能検査で左右差が観察されました。参考測定ですが、差が続く場合は眼科で確認してください。",
  find_vt_ok: "機能検査で左右の明らかな差は観察されませんでした（参考測定）。",
  find_vt_unmeasurable: "片方の目は最大の視標も判別できませんでした。測定条件の問題の可能性もありますが、左右差が大きい可能性があり受診をお勧めします。",
  vt_cross_match: "📌 写真解析でも左右差の所見がありました（いずれも参考情報です）。",
  tri_factors: "定期検診をお勧めする理由: {items}",
  save_saving: "保存中...", save_done: "保存しました。",
  save_failed: "保存できませんでした。結果は画面で引き続きご確認いただけます。", save_retry: "再試行",
  calib_stale: "画面設定が変わったようです（回転・ズーム・サイズ）。正確な測定のため再調整してください。"
});
Object.assign(translations.zh, {
  vt_intro_desc: "用屏幕上的视标以参考方式观察双眼差异。不提供临床视力值或诊断。",
  vt_beta_note: "参考性测量。数值会随设备、光线与距离变化，请用于比较双眼而非作为绝对值。",
  find_vt_asym: "功能检查中观察到双眼差异。这是参考性测量，若差异持续请到眼科确认。",
  find_vt_ok: "功能检查未观察到双眼明显差异（参考性测量）。",
  find_vt_unmeasurable: "一只眼连最大的视标也无法辨认。可能与测量条件有关，但双眼差异可能较大，建议就诊。",
  vt_cross_match: "📌 照片分析也显示了单侧差异（两者均为参考信息）。",
  tri_factors: "建议定期检查的原因：{items}",
  save_saving: "保存中...", save_done: "已保存。",
  save_failed: "未能保存。结果仍会显示在屏幕上。", save_retry: "重试",
  calib_stale: "屏幕设置似乎已更改（旋转、缩放、窗口大小）。请重新校准以确保测量准确。"
});
