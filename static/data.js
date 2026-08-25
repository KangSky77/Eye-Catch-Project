const translations = {
    ko: {
        nav_test: "AI 검사", nav_disease: "질환 소개", nav_report: "진단 리포트", nav_map: "병원 찾기",
        intro_title: "당신의 눈 건강,<br>AI가 지켜드립니다", intro_desc: "안구 사진 자동 분석과 전문 문진을 통해 주요 안질환 위험도를 체크합니다.",
        flow_photo: "사진 분석", flow_check: "자가진단", flow_report: "맞춤 리포트",
        start_btn: "분석 시작하기", upload_title: "사진 업로드", upload_btn: "사진 선택 및 전송",
        guide_title: "정확한 분석 가이드", guide_list: "<li>정면에서 촬영하세요.</li><li>빛 반사에 주의하세요.</li>",
        tips_title: "정확한 분석을 위한<br>촬영 꿀팁", tip1_t: "전면보다는 후면 카메라!", tip1_d: "후면 카메라가 화질이 좋고 빛 반사가 적어요.", tip2_t: "플래시는 꺼주세요", tip2_d: "플래시 반사가 눈동자에 하얗게 맺히면 혼탁으로 잘못 읽힐 수 있어요. 창가나 밝은 실내에서 찍어주세요.", tip3_t: "30cm 거리를 유지하세요", tip3_d: "너무 가까우면 초점이 흐려질 수 있어요.", tips_btn: "이해했습니다!",
        loading_title: "AI 딥러닝 분석 중...", ai_res_title: "백내장 판별 결과", next_amsler: "2단계: 황반변성 테스트",
        ams_title: "황반변성 자가진단", ams_ok: "정상 (곧게 보임)", ams_bad: "휘어보임/암점",
        chat_yes: "네", chat_no: "아니오", dis_main_title: "4대 주요 안질환 안내", rep_title: "Eye-Catch 진단 리포트",
        rep_l1: "1. 백내장 AI 결과", rep_l2: "2. 황반변성 결과", rep_l3: "3. 문진 소견", rep_l4: "4. Gemma AI 맞춤 소견", pdf_btn: "PDF 다운로드", map_btn: "내 주변 안과 찾기",
        msg_gen: "리포트를 생성 중입니다...", res_ams_bad: "이상 소견 (검사 요망)", res_ams_ok: "특이사항 없음", res_chat_none: "주요 증상 없음",
        rep_warn: "본 리포트는 AI 자가진단 보조 자료입니다. 정확한 진단을 위해 안과 전문의와 상담하시기 바랍니다.",
        dis_card_hint: "카드를 누르면 자세한 설명을 확인할 수 있어요.", dis_more: "자세히 보기 →", dis_modal_note: "이런 증상이 의심되면 안과 검진을 받아보세요.", dm_close: "닫기", dis_ai_badge: "AI 분석 지원",
        dis_modal_image: "임상 참고 이미지", dis_modal_symptoms: "주요 증상", dis_modal_risk: "위험 요인", dis_modal_care: "검사와 치료", dis_modal_urgent: "빠른 진료가 필요한 경우", dis_modal_source: "공식 질환 정보", dis_modal_image_note: "교육용 참고 이미지이며 사진만으로 질환을 진단할 수 없습니다.", dis_modal_image_source: "이미지 원본", dis_modal_license: "라이선스", dis_modal_image_change_reencoded: "변경 사항: 960px 썸네일을 PNG에서 JPEG로 재인코딩했습니다(품질 85). 내용 편집·크롭은 하지 않았습니다.",
        dis_modal_image_external: "외안부 사진", dis_modal_image_fundus: "안저 사진 · 병원 장비 필요", dis_modal_image_fundus_note: "눈 안쪽 망막에 생기는 질환이라 겉모습으로는 확인할 수 없고, 앱의 사진 분석 대상도 아닙니다.",
        map_page_title: "내 주변 안과 찾기", map_locate: "내 위치로 찾기", map_open_full: "카카오맵에서 전체 보기",
        map_status_idle: "아래 버튼을 눌러 가까운 안과를 찾아보세요.", map_status_loading: "위치를 확인하는 중...", map_status_denied: "위치 권한이 거부되었어요. 전체 지도에서 검색해 주세요.", map_status_unsupported: "이 브라우저는 위치 기능을 지원하지 않아요.",
        map_status_unavailable: "현재 위치를 확인할 수 없어요. 잠시 후 다시 시도해 주세요.", map_status_timeout: "위치 확인 시간이 초과됐어요. 다시 시도해 주세요.",
        map_you: "내 위치", map_searching: "주변 안과를 찾는 중... ⏳", map_found: "주변 안과 {n}곳을 찾았어요.", map_none: "주변에서 안과를 찾지 못했어요. 전체 지도에서 검색해 주세요.", map_search_err: "안과 검색에 실패했어요. 전체 지도에서 검색해 주세요.", map_directions: "길찾기",
        ai_normal: "특이 소견 없음 (정상)", ai_risk: "백내장 위험 단계 (정밀 검사 권장)", ai_borderline: "경계 단계 (재촬영 후 재검사 또는 안과 검진 권장)", ai_invalid: "눈 사진이 아닌 것 같아요. 눈을 가까이서 촬영한 사진을 올려주세요.",
        face_mode_note: "얼굴 사진에서 눈 {n}곳을 찾아 분석했어요.",
        eye_breakdown_title: "눈별 분석 (사진 기준)", eye_left: "왼쪽 눈", eye_right: "오른쪽 눈", eye_unilateral: "편측 의심 — 한쪽 눈만 위험 신호", eye_ref_note: "※ 얼굴 사진의 눈별 수치는 참고용이며, 정확도는 눈 클로즈업 촬영이 더 높습니다.",
        loading_elapsed: "{s}초 경과",
        loading_uploading: "사진 업로드 중", loading_analyzing: "AI가 분석 중", loading_slow_hint: "네트워크가 느리면 조금 더 걸릴 수 있어요.",
        chat_free_label: "자유롭게 답해 주세요", chat_free_ph: "답변을 입력해 주세요", chat_free_send: "보내기", chat_free_skip: "건너뛰기",
        gemma_idle: "먼저 'AI 검사'를 진행하면 맞춤 소견이 여기에 표시됩니다.", rep_followup_title: "AI에게 더 궁금한 점 물어보기", rep_followup_ph: "예: 관리 방법 알려줘",
        srv_err: "서버와 연결할 수 없습니다.", nextq_fallback: "추가적으로 눈이 불편하신 곳이 있나요?",
        survey_done: "기본 문진이 완료되었습니다. 맞춤형 추가 질문을 생성 중입니다... ⏳", next_q_generating: "다음 맞춤형 질문을 생성 중입니다... ⏳", symptom_extra: "기타 의심 증상 추가 발견",
        opinion_writing: "AI가 소견서를 작성 중입니다...\n\n", opinion_error: "로컬 AI 서버와 연결이 끊어졌습니다.",
        notif_title: "Eye-Catch 진단 완료", notif_body: "AI 맞춤형 소견서 작성이 완료되었습니다! 결과를 확인해보세요.", followup_thinking: "답변을 생각하고 있습니다...\n\n",
        pdf_doc_title: "Eye-Catch 정밀 진단 리포트", pdf_issued: "발급일자", pdf_s1: "1. 백내장 AI 분석 결과", pdf_s2: "2. 황반변성 자가진단 (Amsler Grid)", pdf_s3: "3. AI 문진 주요 소견", pdf_s4: "4. 종합 AI 소견서 (Powered by Gemma)",
        pdf_footer: "본 리포트는 인공지능 기반의 자가진단 보조 자료입니다.<br>정확한 진단 및 처방을 위해서는 반드시 안과 전문의와 상담하시기 바랍니다.",
        back_btn: "← 이전", step_progress: "{total}단계 중 {n}단계",
        ams_howto: "한쪽 눈을 가리고 약 30cm 거리에서 가운데 점을 바라보세요. 반대쪽 눈도 같은 방법으로 확인합니다.",
        err_file_type: "이미지 파일만 올릴 수 있어요.", err_file_size: "사진 용량이 너무 커요. {n}MB 이하 사진을 올려주세요.",
        pdf_making: "PDF를 만드는 중...", pdf_err: "PDF 생성에 실패했어요. 잠시 후 다시 시도해 주세요.",
        aria_lang: "언어 선택", aria_send: "질문 보내기", aria_home: "처음 화면으로", aria_nav_main: "주 메뉴", aria_flow: "검사 진행 과정",
        report_hint_empty: "아직 검사 결과가 없어요. 'AI 검사'부터 진행해 주세요.",
        skip_to_content: "본문으로 건너뛰기", upload_drop_hint: "여기로 사진을 끌어다 놓아도 됩니다.", retry_photo: "← 다른 사진으로 다시 분석"
    },
    en: {
        nav_test: "AI Analysis", nav_disease: "Diseases", nav_report: "Report", nav_map: "Find Clinic",
        intro_title: "Your Eye Health,<br>Protected by AI", intro_desc: "AI photo analysis and survey to check major eye disease risks.",
        flow_photo: "Photo analysis", flow_check: "Self-check", flow_report: "Personal report",
        start_btn: "Start Analysis", upload_title: "Upload Photo", upload_btn: "Select & Send",
        guide_title: "Analysis Guide", guide_list: "<li>Face front.</li><li>Avoid glare/reflections.</li>",
        tips_title: "Photo Tips for<br>Accurate Analysis", tip1_t: "Use the rear camera!", tip1_d: "The rear camera has better quality and less glare.", tip2_t: "Turn the flash off", tip2_d: "A flash reflection on the pupil can be misread as clouding. Shoot in window light or a well-lit room instead.", tip3_t: "Keep about 30cm distance", tip3_d: "Too close and the photo may be out of focus.", tips_btn: "Got it!",
        loading_title: "AI Analyzing...", ai_res_title: "Cataract Result", next_amsler: "Step 2: Macular Test",
        ams_title: "Amsler Grid Test", ams_ok: "Normal (Straight)", ams_bad: "Distorted/Spot",
        chat_yes: "Yes", chat_no: "No", dis_main_title: "Major Eye Diseases", rep_title: "Eye-Catch Diagnostic Report",
        rep_l1: "1. Cataract AI", rep_l2: "2. Macular Test", rep_l3: "3. Survey Result", rep_l4: "4. Gemma AI Personalized Opinion", pdf_btn: "Download PDF", map_btn: "Find a Clinic",
        msg_gen: "Generating report...", res_ams_bad: "Distortion detected", res_ams_ok: "Normal", res_chat_none: "No symptoms",
        rep_warn: "This is an AI-assisted tool. Please consult an ophthalmologist for an accurate diagnosis.",
        dis_card_hint: "Tap a card to see the full description.", dis_more: "Learn more →", dis_modal_note: "If you notice these symptoms, please see an ophthalmologist.", dm_close: "Close", dis_ai_badge: "AI-Powered",
        dis_modal_image: "Clinical reference image", dis_modal_symptoms: "Common symptoms", dis_modal_risk: "Risk factors", dis_modal_care: "Exams and treatment", dis_modal_urgent: "When to seek prompt care", dis_modal_source: "Official condition guide", dis_modal_image_note: "For education only. A condition cannot be diagnosed from a photo alone.", dis_modal_image_source: "Image source", dis_modal_license: "License", dis_modal_image_change_reencoded: "Change: the 960 px thumbnail was re-encoded from PNG to JPEG (quality 85), with no content edits or cropping.",
        dis_modal_image_external: "External eye photo", dis_modal_image_fundus: "Fundus photo · clinic equipment needed", dis_modal_image_fundus_note: "This develops on the retina inside the eye, so it is invisible from the outside and is not covered by the app photo analysis.",
        map_page_title: "Find a Clinic Near You", map_locate: "Use My Location", map_open_full: "Open Full Map",
        map_status_idle: "Tap the button below to find nearby eye clinics.", map_status_loading: "Locating you...", map_status_denied: "Location denied. Please search on the full map.", map_status_unsupported: "This browser does not support geolocation.",
        map_status_unavailable: "Your location is currently unavailable. Please try again shortly.", map_status_timeout: "Location lookup timed out. Please try again.",
        map_you: "You are here", map_searching: "Searching nearby eye clinics... ⏳", map_found: "Found {n} eye clinic(s) nearby.", map_none: "No eye clinics found nearby. Please search on the full map.", map_search_err: "Search failed. Please use the full map.", map_directions: "Directions",
        ai_normal: "No significant findings (Normal)", ai_risk: "Cataract risk stage (Detailed exam recommended)", ai_borderline: "Borderline (Retake the photo or consider an eye exam)", ai_invalid: "This doesn't look like an eye photo. Please upload a close-up of your eye.",
        face_mode_note: "Detected {n} eye(s) in the face photo and analyzed them.",
        eye_breakdown_title: "Per-eye analysis (as in photo)", eye_left: "Left eye", eye_right: "Right eye", eye_unilateral: "Possible one-sided (unilateral) — only one eye flagged", eye_ref_note: "※ Per-eye values from a face photo are for reference; a close-up of the eye is more accurate.",
        loading_elapsed: "{s}s elapsed",
        loading_uploading: "Uploading photo", loading_analyzing: "AI is analyzing", loading_slow_hint: "This can take longer on a slow network.",
        chat_free_label: "Answer in your own words", chat_free_ph: "Type your answer", chat_free_send: "Send", chat_free_skip: "Skip",
        gemma_idle: "Complete the AI analysis first to see your personalized opinion here.", rep_followup_title: "Ask the AI more questions", rep_followup_ph: "e.g. How should I care for my eyes?",
        srv_err: "Unable to connect to the server.", nextq_fallback: "Is there anything else bothering your eyes?",
        survey_done: "Basic survey complete. Generating a personalized follow-up question... ⏳", next_q_generating: "Generating the next personalized question... ⏳", symptom_extra: "Additional suspected symptom found",
        opinion_writing: "The AI is writing your opinion...\n\n", opinion_error: "Connection to the local AI server was lost.",
        notif_title: "Eye-Catch Diagnosis Complete", notif_body: "Your personalized AI opinion is ready! Check your results.", followup_thinking: "Thinking of an answer...\n\n",
        pdf_doc_title: "Eye-Catch Diagnostic Report", pdf_issued: "Issued", pdf_s1: "1. Cataract AI Analysis", pdf_s2: "2. Macular Self-Test (Amsler Grid)", pdf_s3: "3. AI Survey Findings", pdf_s4: "4. Comprehensive AI Opinion (Powered by Gemma)",
        pdf_footer: "This report is an AI-assisted self-screening aid.<br>Please consult an ophthalmologist for an accurate diagnosis and treatment.",
        back_btn: "← Back", step_progress: "Step {n} of {total}",
        ams_howto: "Cover one eye and look at the center dot from about 30 cm away. Then repeat with the other eye.",
        err_file_type: "Please upload an image file.", err_file_size: "That photo is too large. Please upload a file under {n} MB.",
        pdf_making: "Creating your PDF...", pdf_err: "Could not create the PDF. Please try again.",
        aria_lang: "Select language", aria_send: "Send question", aria_home: "Back to start", aria_nav_main: "Main menu", aria_flow: "Screening steps",
        report_hint_empty: "No results yet. Run the AI analysis first.",
        skip_to_content: "Skip to content", upload_drop_hint: "You can also drag and drop a photo here.", retry_photo: "← Analyze another photo"
    },
    es: {
        nav_test: "Análisis IA", nav_disease: "Enfermedades", nav_report: "Informe", nav_map: "Clínicas",
        intro_title: "Tu salud ocular,<br>protegida por IA", intro_desc: "Análisis de fotos y encuesta para detectar riesgos oculares.",
        flow_photo: "Análisis de foto", flow_check: "Autoevaluación", flow_report: "Informe personal",
        start_btn: "Iniciar análisis", upload_title: "Subir foto", upload_btn: "Seleccionar foto",
        guide_title: "Guía", guide_list: "<li>Mira al frente.</li><li>Evita reflejos.</li>",
        tips_title: "Consejos de foto para<br>un análisis preciso", tip1_t: "¡Use la cámara trasera!", tip1_d: "La cámara trasera tiene mejor calidad y menos reflejos.", tip2_t: "Apague el flash", tip2_d: "El reflejo del flash sobre la pupila puede confundirse con opacidad. Use luz de ventana o una sala bien iluminada.", tip3_t: "Mantenga unos 30 cm de distancia", tip3_d: "Si está muy cerca, la foto puede salir desenfocada.", tips_btn: "¡Entendido!",
        loading_title: "IA analizando...", ai_res_title: "Resultado de Cataratas", next_amsler: "Paso 2: Mácula",
        ams_title: "Prueba de Amsler", ams_ok: "Normal (Recto)", ams_bad: "Distorsionado/Mancha",
        chat_yes: "Sí", chat_no: "No", dis_main_title: "Enfermedades Oculares", rep_title: "Informe Diagnóstico Eye-Catch",
        rep_l1: "1. IA de Cataratas", rep_l2: "2. Prueba Macular", rep_l3: "3. Encuesta", rep_l4: "4. Opinión de Gemma AI", pdf_btn: "Descargar PDF", map_btn: "Buscar clínica",
        msg_gen: "Generando informe...", res_ams_bad: "Distorsión", res_ams_ok: "Normal", res_chat_none: "Sin síntomas",
        rep_warn: "Herramienta asistida por IA. Consulte a un oftalmólogo para un diagnóstico preciso.",
        dis_card_hint: "Toca una tarjeta para ver la descripción completa.", dis_more: "Ver más →", dis_modal_note: "Si nota estos síntomas, consulte a un oftalmólogo.", dm_close: "Cerrar", dis_ai_badge: "Análisis con IA",
        dis_modal_image: "Imagen clínica de referencia", dis_modal_symptoms: "Síntomas frecuentes", dis_modal_risk: "Factores de riesgo", dis_modal_care: "Pruebas y tratamiento", dis_modal_urgent: "Cuándo buscar atención rápida", dis_modal_source: "Guía oficial", dis_modal_image_note: "Solo con fines educativos. Una foto por sí sola no permite diagnosticar.", dis_modal_image_source: "Fuente de la imagen", dis_modal_license: "Licencia", dis_modal_image_change_reencoded: "Cambio: la miniatura de 960 px se recodificó de PNG a JPEG (calidad 85), sin editar ni recortar el contenido.",
        dis_modal_image_external: "Foto ocular externa", dis_modal_image_fundus: "Retinografía · requiere equipo clínico", dis_modal_image_fundus_note: "Se desarrolla en la retina, dentro del ojo, por lo que no se ve desde fuera ni lo cubre el análisis de fotos de la app.",
        map_page_title: "Encontrar una clínica cercana", map_locate: "Usar mi ubicación", map_open_full: "Abrir mapa completo",
        map_status_idle: "Pulse el botón para encontrar clínicas cercanas.", map_status_loading: "Localizando...", map_status_denied: "Ubicación denegada. Busque en el mapa completo.", map_status_unsupported: "Este navegador no admite geolocalización.",
        map_status_unavailable: "Su ubicación no está disponible en este momento. Inténtelo de nuevo en breve.", map_status_timeout: "La búsqueda de ubicación agotó el tiempo. Inténtelo de nuevo.",
        map_you: "Estás aquí", map_searching: "Buscando clínicas cercanas... ⏳", map_found: "{n} clínica(s) oftalmológica(s) cerca.", map_none: "No se encontraron clínicas cerca. Busque en el mapa completo.", map_search_err: "Búsqueda fallida. Use el mapa completo.", map_directions: "Cómo llegar",
        ai_normal: "Sin hallazgos significativos (Normal)", ai_risk: "Riesgo de cataratas (Se recomienda examen detallado)", ai_borderline: "Resultado límite (Repita la foto o considere un examen ocular)", ai_invalid: "Esto no parece una foto de un ojo. Suba un primer plano de su ojo.",
        face_mode_note: "Se detectaron {n} ojo(s) en la foto del rostro y se analizaron.",
        eye_breakdown_title: "Análisis por ojo (según la foto)", eye_left: "Ojo izquierdo", eye_right: "Ojo derecho", eye_unilateral: "Posible unilateral — solo un ojo con señal de riesgo", eye_ref_note: "※ Los valores por ojo de una foto del rostro son orientativos; un primer plano del ojo es más preciso.",
        loading_elapsed: "{s} s transcurridos",
        loading_uploading: "Subiendo la foto", loading_analyzing: "La IA está analizando", loading_slow_hint: "Puede tardar más si la red es lenta.",
        chat_free_label: "Responda con sus palabras", chat_free_ph: "Escriba su respuesta", chat_free_send: "Enviar", chat_free_skip: "Omitir",
        gemma_idle: "Completa primero el análisis de IA para ver aquí tu opinión personalizada.", rep_followup_title: "Haz más preguntas a la IA", rep_followup_ph: "ej. ¿Cómo cuido mis ojos?",
        srv_err: "No se puede conectar con el servidor.", nextq_fallback: "¿Hay algo más que le moleste en los ojos?",
        survey_done: "Encuesta básica completada. Generando una pregunta personalizada... ⏳", next_q_generating: "Generando la siguiente pregunta personalizada... ⏳", symptom_extra: "Síntoma sospechoso adicional encontrado",
        opinion_writing: "La IA está redactando su informe...\n\n", opinion_error: "Se perdió la conexión con el servidor de IA local.",
        notif_title: "Diagnóstico Eye-Catch completado", notif_body: "¡Su informe de IA personalizado está listo! Revise sus resultados.", followup_thinking: "Pensando una respuesta...\n\n",
        pdf_doc_title: "Informe Diagnóstico Eye-Catch", pdf_issued: "Fecha de emisión", pdf_s1: "1. Análisis de Cataratas por IA", pdf_s2: "2. Autoprueba Macular (Rejilla de Amsler)", pdf_s3: "3. Hallazgos de la Encuesta IA", pdf_s4: "4. Opinión Integral de IA (Powered by Gemma)",
        pdf_footer: "Este informe es una ayuda de autodetección asistida por IA.<br>Consulte a un oftalmólogo para un diagnóstico y tratamiento precisos.",
        back_btn: "← Atrás", step_progress: "Paso {n} de {total}",
        ams_howto: "Tápese un ojo y mire el punto central a unos 30 cm. Repita con el otro ojo.",
        err_file_type: "Suba un archivo de imagen.", err_file_size: "La foto es demasiado grande. Suba un archivo de menos de {n} MB.",
        pdf_making: "Creando el PDF...", pdf_err: "No se pudo crear el PDF. Inténtelo de nuevo.",
        aria_lang: "Seleccionar idioma", aria_send: "Enviar pregunta", aria_home: "Volver al inicio", aria_nav_main: "Menú principal", aria_flow: "Pasos del examen",
        report_hint_empty: "Aún no hay resultados. Realice primero el análisis con IA.",
        skip_to_content: "Ir al contenido", upload_drop_hint: "También puede arrastrar y soltar una foto aquí.", retry_photo: "← Analizar otra foto"
    },
    fr: {
        nav_test: "Analyse IA", nav_disease: "Maladies", nav_report: "Rapport", nav_map: "Trouver Clinique",
        intro_title: "Votre santé oculaire,<br>protégée par l'IA", intro_desc: "Analyse photo et sondage pour détecter les risques oculaires.",
        flow_photo: "Analyse photo", flow_check: "Auto-évaluation", flow_report: "Rapport personnel",
        start_btn: "Démarrer l'analyse", upload_title: "Télécharger Photo", upload_btn: "Sélectionner Photo",
        guide_title: "Guide", guide_list: "<li>Regardez de face.</li><li>Évitez les reflets.</li>",
        tips_title: "Conseils photo pour<br>une analyse précise", tip1_t: "Utilisez la caméra arrière !", tip1_d: "La caméra arrière offre une meilleure qualité et moins de reflets.", tip2_t: "Désactivez le flash", tip2_d: "Un reflet de flash sur la pupille peut être pris pour une opacité. Photographiez près d'une fenêtre ou dans une pièce bien éclairée.", tip3_t: "Gardez environ 30 cm de distance", tip3_d: "Trop près, la photo peut être floue.", tips_btn: "Compris !",
        loading_title: "IA en analyse...", ai_res_title: "Résultat Cataracte", next_amsler: "Étape 2: Macula",
        ams_title: "Test de la grille d'Amsler", ams_ok: "Normal (Droit)", ams_bad: "Déformé/Tache",
        chat_yes: "Oui", chat_no: "Non", dis_main_title: "Maladies Oculaires", rep_title: "Rapport de Diagnostic Eye-Catch",
        rep_l1: "1. IA Cataracte", rep_l2: "2. Test Maculaire", rep_l3: "3. Sondage", rep_l4: "4. Avis de Gemma AI", pdf_btn: "Télécharger PDF", map_btn: "Trouver une clinique",
        msg_gen: "Génération du rapport...", res_ams_bad: "Distorsion", res_ams_ok: "Normal", res_chat_none: "Aucun symptôme",
        rep_warn: "Outil assisté par IA. Veuillez consulter un ophtalmologiste.",
        dis_card_hint: "Appuyez sur une carte pour voir la description complète.", dis_more: "En savoir plus →", dis_modal_note: "Si vous remarquez ces symptômes, consultez un ophtalmologiste.", dm_close: "Fermer", dis_ai_badge: "Analyse par IA",
        dis_modal_image: "Image clinique de référence", dis_modal_symptoms: "Symptômes fréquents", dis_modal_risk: "Facteurs de risque", dis_modal_care: "Examens et traitement", dis_modal_urgent: "Quand consulter rapidement", dis_modal_source: "Guide officiel", dis_modal_image_note: "Image éducative uniquement. Une photo seule ne permet pas de poser un diagnostic.", dis_modal_image_source: "Source de l’image", dis_modal_license: "Licence", dis_modal_image_change_reencoded: "Modification : la vignette de 960 px a été réencodée du PNG au JPEG (qualité 85), sans retouche ni recadrage.",
        dis_modal_image_external: "Photo oculaire externe", dis_modal_image_fundus: "Rétinographie · équipement clinique requis", dis_modal_image_fundus_note: "Cette atteinte se développe sur la rétine, à l'intérieur de l'œil : invisible de l'extérieur, elle n'est pas couverte par l'analyse photo de l'app.",
        map_page_title: "Trouver une clinique près de chez vous", map_locate: "Utiliser ma position", map_open_full: "Ouvrir la carte complète",
        map_status_idle: "Appuyez sur le bouton pour trouver des cliniques proches.", map_status_loading: "Localisation...", map_status_denied: "Position refusée. Recherchez sur la carte complète.", map_status_unsupported: "Ce navigateur ne prend pas en charge la géolocalisation.",
        map_status_unavailable: "Votre position est actuellement indisponible. Réessayez dans un instant.", map_status_timeout: "La recherche de position a expiré. Veuillez réessayer.",
        map_you: "Vous êtes ici", map_searching: "Recherche de cliniques proches... ⏳", map_found: "{n} clinique(s) ophtalmologique(s) à proximité.", map_none: "Aucune clinique trouvée à proximité. Utilisez la carte complète.", map_search_err: "Échec de la recherche. Utilisez la carte complète.", map_directions: "Itinéraire",
        ai_normal: "Aucune anomalie notable (Normal)", ai_risk: "Stade de risque de cataracte (Examen approfondi recommandé)", ai_borderline: "Résultat limite (Reprenez la photo ou envisagez un examen ophtalmologique)", ai_invalid: "Cela ne ressemble pas à une photo d'œil. Veuillez téléverser un gros plan de votre œil.",
        face_mode_note: "{n} œil/yeux détecté(s) sur la photo du visage et analysé(s).",
        eye_breakdown_title: "Analyse par œil (selon la photo)", eye_left: "Œil gauche", eye_right: "Œil droit", eye_unilateral: "Possiblement unilatéral — un seul œil signalé", eye_ref_note: "※ Les valeurs par œil issues d'une photo du visage sont indicatives ; un gros plan de l'œil est plus précis.",
        loading_elapsed: "{s} s écoulées",
        loading_uploading: "Envoi de la photo", loading_analyzing: "L'IA analyse", loading_slow_hint: "Cela peut être plus long si le réseau est lent.",
        chat_free_label: "Répondez avec vos mots", chat_free_ph: "Saisissez votre réponse", chat_free_send: "Envoyer", chat_free_skip: "Passer",
        gemma_idle: "Effectuez d'abord l'analyse IA pour voir votre avis personnalisé ici.", rep_followup_title: "Posez plus de questions à l'IA", rep_followup_ph: "ex. Comment prendre soin de mes yeux ?",
        srv_err: "Impossible de se connecter au serveur.", nextq_fallback: "Y a-t-il autre chose qui vous gêne aux yeux ?",
        survey_done: "Questionnaire de base terminé. Génération d'une question personnalisée... ⏳", next_q_generating: "Génération de la prochaine question personnalisée... ⏳", symptom_extra: "Symptôme suspect supplémentaire détecté",
        opinion_writing: "L'IA rédige votre avis...\n\n", opinion_error: "La connexion au serveur IA local a été perdue.",
        notif_title: "Diagnostic Eye-Catch terminé", notif_body: "Votre avis IA personnalisé est prêt ! Consultez vos résultats.", followup_thinking: "Réflexion à une réponse...\n\n",
        pdf_doc_title: "Rapport de Diagnostic Eye-Catch", pdf_issued: "Date d'émission", pdf_s1: "1. Analyse Cataracte par IA", pdf_s2: "2. Autotest Maculaire (Grille d'Amsler)", pdf_s3: "3. Conclusions du Questionnaire IA", pdf_s4: "4. Avis Global de l'IA (Powered by Gemma)",
        pdf_footer: "Ce rapport est une aide d'auto-dépistage assistée par IA.<br>Veuillez consulter un ophtalmologiste pour un diagnostic et un traitement précis.",
        back_btn: "← Retour", step_progress: "Étape {n} sur {total}",
        ams_howto: "Couvrez un œil et fixez le point central à environ 30 cm. Répétez avec l'autre œil.",
        err_file_type: "Veuillez importer un fichier image.", err_file_size: "Cette photo est trop volumineuse. Importez un fichier de moins de {n} Mo.",
        pdf_making: "Création du PDF...", pdf_err: "Impossible de créer le PDF. Veuillez réessayer.",
        aria_lang: "Choisir la langue", aria_send: "Envoyer la question", aria_home: "Revenir au début", aria_nav_main: "Menu principal", aria_flow: "Étapes du dépistage",
        report_hint_empty: "Aucun résultat pour l'instant. Lancez d'abord l'analyse IA.",
        skip_to_content: "Aller au contenu", upload_drop_hint: "Vous pouvez aussi glisser-déposer une photo ici.", retry_photo: "← Analyser une autre photo"
    },
    ja: {
        nav_test: "AI検査", nav_disease: "眼疾患について", nav_report: "診断レポート", nav_map: "病院検索",
        intro_title: "あなたの目の健康、<br>AIがお守りします", intro_desc: "AI写真分析と問診で主要な眼疾患のリスクをチェックします。",
        flow_photo: "写真分析", flow_check: "セルフチェック", flow_report: "個別レポート",
        start_btn: "検査開始", upload_title: "写真アップロード", upload_btn: "写真を選択して送信",
        guide_title: "正確な分析のために", guide_list: "<li>正面から撮影してください。</li><li>光の反射に注意してください。</li>",
        tips_title: "正確な分析のための<br>撮影のコツ", tip1_t: "前面より背面カメラで！", tip1_d: "背面カメラの方が画質が良く、光の反射も少ないです。", tip2_t: "フラッシュはオフに", tip2_d: "フラッシュの反射が瞳に白く写ると、濁りと誤読されることがあります。窓際や明るい室内で撮ってください。", tip3_t: "30cmの距離を保って", tip3_d: "近すぎるとピントがぼやけることがあります。", tips_btn: "わかりました！",
        loading_title: "AI分析中...", ai_res_title: "白内障判定結果", next_amsler: "ステップ2：黄斑変性テスト",
        ams_title: "アムスラーグリッドテスト", ams_ok: "正常（まっすぐ）", ams_bad: "歪み/暗点",
        chat_yes: "はい", chat_no: "いいえ", dis_main_title: "4大眼疾患について", rep_title: "Eye-Catch 診断レポート",
        rep_l1: "1. 白内障AI結果", rep_l2: "2. 黄斑変性結果", rep_l3: "3. 問診結果", rep_l4: "4. Gemma AIカスタム所見", pdf_btn: "PDFダウンロード", map_btn: "病院を探す",
        msg_gen: "レポートを作成中...", res_ams_bad: "異常あり（要検査）", res_ams_ok: "特記事項なし", res_chat_none: "主要な症状なし",
        rep_warn: "本レポートはAIによる補助資料です。正確な診断のため眼科を受診してください。",
        dis_card_hint: "カードをタップすると詳しい説明が見られます。", dis_more: "詳しく見る →", dis_modal_note: "このような症状があれば眼科を受診してください。", dm_close: "閉じる", dis_ai_badge: "AI分析対応",
        dis_modal_image: "臨床参考画像", dis_modal_symptoms: "主な症状", dis_modal_risk: "リスク因子", dis_modal_care: "検査と治療", dis_modal_urgent: "早めの受診が必要な場合", dis_modal_source: "公的な疾患情報", dis_modal_image_note: "教育用の参考画像です。写真だけで診断することはできません。", dis_modal_image_source: "画像の出典", dis_modal_license: "ライセンス", dis_modal_image_change_reencoded: "変更点：960pxのサムネイルをPNGからJPEG（品質85）へ再エンコードしました。内容の編集やトリミングはしていません。",
        dis_modal_image_external: "外眼部写真", dis_modal_image_fundus: "眼底写真 · 医療機器が必要", dis_modal_image_fundus_note: "眼の内側の網膜に生じるため外見では確認できず、アプリの写真分析の対象外です。",
        map_page_title: "近くの眼科を探す", map_locate: "現在地で探す", map_open_full: "地図全体を開く",
        map_status_idle: "下のボタンを押して近くの眼科を探しましょう。", map_status_loading: "現在地を確認中...", map_status_denied: "位置情報が拒否されました。地図全体で検索してください。", map_status_unsupported: "このブラウザは位置情報に対応していません。",
        map_status_unavailable: "現在地を確認できません。しばらくしてからもう一度お試しください。", map_status_timeout: "位置情報の確認がタイムアウトしました。もう一度お試しください。",
        map_you: "現在地", map_searching: "近くの眼科を検索中... ⏳", map_found: "近くに眼科が{n}件見つかりました。", map_none: "近くに眼科が見つかりませんでした。地図全体で検索してください。", map_search_err: "検索に失敗しました。地図全体で検索してください。", map_directions: "経路",
        ai_normal: "特記所見なし（正常）", ai_risk: "白内障リスク段階（精密検査を推奨）", ai_borderline: "境界域（再撮影または眼科検診を推奨）", ai_invalid: "目の写真ではないようです。目のクローズアップ写真をアップロードしてください。",
        face_mode_note: "顔写真から目を{n}箇所検出して分析しました。",
        eye_breakdown_title: "目ごとの分析（写真基準）", eye_left: "左目", eye_right: "右目", eye_unilateral: "片側の疑い — 片方の目だけ危険信号", eye_ref_note: "※ 顔写真の目ごとの数値は参考用で、目のクローズアップ撮影の方が精度が高いです。",
        loading_elapsed: "{s}秒経過",
        loading_uploading: "写真をアップロード中", loading_analyzing: "AIが分析中", loading_slow_hint: "通信が遅いと時間がかかることがあります。",
        chat_free_label: "自由にお答えください", chat_free_ph: "回答を入力してください", chat_free_send: "送信", chat_free_skip: "スキップ",
        gemma_idle: "先にAI検査を完了すると、ここにカスタム所見が表示されます。", rep_followup_title: "AIにもっと質問する", rep_followup_ph: "例：ケア方法を教えて",
        srv_err: "サーバーに接続できません。", nextq_fallback: "他に目で気になるところはありますか？",
        survey_done: "基本問診が完了しました。カスタム追加質問を生成中です... ⏳", next_q_generating: "次のカスタム質問を生成中です... ⏳", symptom_extra: "その他の疑わしい症状を追加検出",
        opinion_writing: "AIが所見を作成中です...\n\n", opinion_error: "ローカルAIサーバーとの接続が切れました。",
        notif_title: "Eye-Catch 診断完了", notif_body: "AIによるカスタム所見が完成しました！結果をご確認ください。", followup_thinking: "回答を考えています...\n\n",
        pdf_doc_title: "Eye-Catch 精密診断レポート", pdf_issued: "発行日", pdf_s1: "1. 白内障 AI 分析結果", pdf_s2: "2. 黄斑自己検査（アムスラーグリッド）", pdf_s3: "3. AI問診の主な所見", pdf_s4: "4. 総合AI所見（Powered by Gemma）",
        pdf_footer: "本レポートはAIによる自己スクリーニング補助資料です。<br>正確な診断と治療のため、必ず眼科医にご相談ください。",
        back_btn: "← 戻る", step_progress: "{total}ステップ中 {n}ステップ目",
        ams_howto: "片目を手で覆い、約30cm離れて中央の点を見つめてください。反対の目も同じように確認します。",
        err_file_type: "画像ファイルのみアップロードできます。", err_file_size: "写真のサイズが大きすぎます。{n}MB以下のファイルをアップロードしてください。",
        pdf_making: "PDFを作成中...", pdf_err: "PDFの作成に失敗しました。しばらくしてからもう一度お試しください。",
        aria_lang: "言語を選択", aria_send: "質問を送信", aria_home: "最初の画面へ", aria_nav_main: "メインメニュー", aria_flow: "検査の流れ",
        report_hint_empty: "まだ検査結果がありません。先にAI検査を行ってください。",
        skip_to_content: "本文へスキップ", upload_drop_hint: "ここに写真をドラッグ＆ドロップすることもできます。", retry_photo: "← 別の写真で再分析"
    },
    zh: {
        nav_test: "AI检测", nav_disease: "疾病介绍", nav_report: "诊断报告", nav_map: "寻找医院",
        intro_title: "您的眼部健康，<br>由AI来守护", intro_desc: "通过AI照片分析和问卷调查检查主要眼部疾病风险。",
        flow_photo: "照片分析", flow_check: "自我检测", flow_report: "个性化报告",
        start_btn: "开始检测", upload_title: "上传照片", upload_btn: "选择并发送照片",
        guide_title: "准确分析指南", guide_list: "<li>请正面拍摄。</li><li>请注意避免反光。</li>",
        tips_title: "拍摄小技巧<br>让分析更准确", tip1_t: "请使用后置摄像头！", tip1_d: "后置摄像头画质更好，反光更少。", tip2_t: "请关闭闪光灯", tip2_d: "闪光灯在瞳孔上的反光可能被误判为混浊。请在窗边或明亮的室内拍摄。", tip3_t: "保持约30厘米距离", tip3_d: "太近可能会导致焦点模糊。", tips_btn: "明白了！",
        loading_title: "AI分析中...", ai_res_title: "白内障判定结果", next_amsler: "第二步：黄斑变性测试",
        ams_title: "阿姆斯勒方格表", ams_ok: "正常（线条笔直）", ams_bad: "扭曲/黑影",
        chat_yes: "是", chat_no: "否", dis_main_title: "四大眼疾介绍", rep_title: "Eye-Catch 综合诊断报告",
        rep_l1: "1. 白内障AI结果", rep_l2: "2. 黄斑变性结果", rep_l3: "3. 问卷结果", rep_l4: "4. Gemma AI 个性化意见", pdf_btn: "下载 PDF", map_btn: "寻找医院",
        msg_gen: "正在生成报告...", res_ams_bad: "发现异常", res_ams_ok: "正常", res_chat_none: "无主要症状",
        rep_warn: "本报告为AI辅助参考资料，为了获得准确诊断，请咨询眼科医生。",
        dis_card_hint: "点击卡片可查看详细说明。", dis_more: "查看详情 →", dis_modal_note: "如有这些症状，请及时就诊眼科。", dm_close: "关闭", dis_ai_badge: "支持AI分析",
        dis_modal_image: "临床参考图片", dis_modal_symptoms: "常见症状", dis_modal_risk: "风险因素", dis_modal_care: "检查与治疗", dis_modal_urgent: "需要尽快就医的情况", dis_modal_source: "官方疾病信息", dis_modal_image_note: "图片仅供健康教育参考，不能仅凭照片诊断疾病。", dis_modal_image_source: "图片来源", dis_modal_license: "许可证", dis_modal_image_change_reencoded: "更改说明：将960像素缩略图从PNG重新编码为JPEG（质量85），未编辑或裁剪内容。",
        dis_modal_image_external: "眼表照片", dis_modal_image_fundus: "眼底照片 · 需医院设备", dis_modal_image_fundus_note: "病变位于眼球内部的视网膜，从外观无法看出，也不在本应用的照片分析范围内。",
        map_page_title: "查找附近的眼科", map_locate: "使用我的位置", map_open_full: "打开完整地图",
        map_status_idle: "点击下方按钮查找附近的眼科。", map_status_loading: "正在确认位置...", map_status_denied: "位置权限被拒绝，请在完整地图中搜索。", map_status_unsupported: "此浏览器不支持定位功能。",
        map_status_unavailable: "目前无法确认您的位置，请稍后重试。", map_status_timeout: "位置确认超时，请重试。",
        map_you: "我的位置", map_searching: "正在搜索附近的眼科... ⏳", map_found: "在附近找到 {n} 家眼科。", map_none: "附近未找到眼科，请在完整地图中搜索。", map_search_err: "搜索失败，请使用完整地图。", map_directions: "路线",
        ai_normal: "无明显异常（正常）", ai_risk: "白内障风险阶段（建议精密检查）", ai_borderline: "临界阶段（建议重新拍摄或进行眼科检查）", ai_invalid: "这看起来不像眼睛照片。请上传眼部特写照片。",
        face_mode_note: "已从面部照片中检测到{n}处眼睛并进行分析。",
        eye_breakdown_title: "逐眼分析（以照片为准）", eye_left: "左眼", eye_right: "右眼", eye_unilateral: "疑似单侧 — 仅一只眼出现风险信号", eye_ref_note: "※ 面部照片的逐眼数值仅供参考，眼部特写拍摄的准确度更高。",
        loading_elapsed: "已用时 {s} 秒",
        loading_uploading: "正在上传照片", loading_analyzing: "AI 正在分析", loading_slow_hint: "网络较慢时可能需要更长时间。",
        chat_free_label: "请用自己的话回答", chat_free_ph: "请输入回答", chat_free_send: "发送", chat_free_skip: "跳过",
        gemma_idle: "请先完成 AI 检测，个性化意见将显示在这里。", rep_followup_title: "向 AI 提出更多问题", rep_followup_ph: "例：如何护理眼睛？",
        srv_err: "无法连接到服务器。", nextq_fallback: "您的眼睛还有其他不适吗？",
        survey_done: "基础问诊已完成。正在生成个性化追加问题... ⏳", next_q_generating: "正在生成下一个个性化问题... ⏳", symptom_extra: "发现其他可疑症状",
        opinion_writing: "AI正在撰写意见书...\n\n", opinion_error: "与本地AI服务器的连接已断开。",
        notif_title: "Eye-Catch 诊断完成", notif_body: "AI个性化意见书已完成！请查看您的结果。", followup_thinking: "正在思考答案...\n\n",
        pdf_doc_title: "Eye-Catch 精密诊断报告", pdf_issued: "签发日期", pdf_s1: "1. 白内障 AI 分析结果", pdf_s2: "2. 黄斑自测（阿姆斯勒方格表）", pdf_s3: "3. AI问诊主要发现", pdf_s4: "4. 综合AI意见书（Powered by Gemma）",
        pdf_footer: "本报告为AI辅助的自我筛查参考资料。<br>为获得准确的诊断和治疗，请务必咨询眼科医生。",
        back_btn: "← 返回", step_progress: "第 {n} 步，共 {total} 步",
        ams_howto: "遮住一只眼睛，在约30厘米处注视中心圆点。然后用另一只眼睛重复。",
        err_file_type: "只能上传图片文件。", err_file_size: "照片太大了。请上传小于 {n}MB 的文件。",
        pdf_making: "正在生成 PDF...", pdf_err: "PDF 生成失败，请稍后重试。",
        aria_lang: "选择语言", aria_send: "发送问题", aria_home: "返回首页", aria_nav_main: "主菜单", aria_flow: "检查流程",
        report_hint_empty: "还没有检查结果，请先进行 AI 检查。",
        skip_to_content: "跳到正文", upload_drop_hint: "也可以把照片拖放到这里。", retry_photo: "← 换一张照片重新分析"
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
// 임상 사진은 로컬에 보관하되 원본 페이지와 라이선스를 함께 노출합니다.
// Public domain 또는 재사용 가능한 Creative Commons 파일만 사용합니다.
const diseaseMedia = [
    {
        src: "/static/assets/diseases/cataract-clinical.jpg",
        kind: "external",
        credit: "Rakesh Ahuja, MD · Wikimedia Commons",
        license: "CC BY-SA 3.0",
        licenseUrl: "https://creativecommons.org/licenses/by-sa/3.0/",
        change: "reencoded",
        page: "https://commons.wikimedia.org/wiki/File:Cataract_in_human_eye.png"
    },
    {
        src: "/static/assets/diseases/amd-fundus.jpg",
        kind: "fundus",
        credit: "National Eye Institute, NIH · Wikimedia Commons",
        license: "Public domain",
        licenseUrl: "https://creativecommons.org/publicdomain/mark/1.0/",
        page: "https://commons.wikimedia.org/wiki/File:Intermediate_age_related_macular_degeneration.jpg"
    },
    {
        src: "/static/assets/diseases/glaucoma-clinical.jpg",
        kind: "external",
        credit: "James Heilman, MD · Wikimedia Commons",
        license: "CC BY-SA 3.0",
        licenseUrl: "https://creativecommons.org/licenses/by-sa/3.0/",
        page: "https://commons.wikimedia.org/wiki/File:Acute_angle_closure_glaucoma.JPG"
    },
    {
        src: "/static/assets/diseases/diabetic-retinopathy-fundus.jpg",
        kind: "fundus",
        credit: "National Eye Institute, NIH · Wikimedia Commons",
        license: "Public domain",
        licenseUrl: "https://creativecommons.org/publicdomain/mark/1.0/",
        page: "https://commons.wikimedia.org/wiki/File:Fundus_retinopathy_EDA03.JPG"
    }
];

const diseaseData = {
    ko: [
        {
            t:"백내장", d:"눈 속 수정체가 혼탁해져 시야가 흐리고 빛이 번져 보이는 질환입니다.",
            detail:"백내장은 눈 표면이 아니라 카메라 렌즈 역할을 하는 수정체가 서서히 혼탁해지는 질환입니다. 대개 천천히 진행하며 양쪽 눈의 진행 속도는 다를 수 있습니다.",
            symptoms:["안개가 낀 듯 흐리거나 겹쳐 보임", "야간 시력 저하, 눈부심과 불빛 주위의 달무리", "색이 바래 보이거나 안경 도수가 자주 변함"],
            risk:"나이가 들수록 흔하며 당뇨, 흡연, 장기간의 스테로이드 사용, 눈 외상·수술 이력이 위험을 높일 수 있습니다.",
            care:"산동 검사를 포함한 종합 안과검사로 확인합니다. 초기에는 도수와 조명을 조절하고, 일상생활에 지장이 커지면 안과 전문의가 수술 시기를 판단합니다.",
            urgent:"갑작스러운 시력 저하, 심한 통증이나 충혈은 일반적인 백내장 증상이 아니므로 바로 안과 진료를 받으세요.",
            caption:"진행된 백내장으로 수정체가 회백색으로 혼탁해 보이는 임상 사진입니다.",
            source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/cataracts"
        },
        {
            t:"황반변성", d:"망막 중심부의 황반이 손상되어 중심 시야가 흐리거나 휘어 보이는 질환입니다.",
            detail:"연령관련 황반변성은 정면을 또렷하게 보는 황반에 변화가 생기는 질환입니다. 건성과 습성으로 나뉘며, 초기에는 증상이 없을 수 있지만 습성은 비교적 빠르게 시력이 떨어질 수 있습니다.",
            symptoms:["직선이나 문틀이 물결처럼 휘어 보임", "중심부가 흐리거나 빈 점·검은 점으로 가려짐", "어두운 곳에서 적응이 늦고 색이 덜 선명해짐"],
            risk:"55세 이상, 흡연, 가족력, 고혈압·고지혈증 등이 위험과 관련됩니다.",
            care:"산동 안저검사와 OCT 등으로 상태와 유형을 확인합니다. 단계에 따라 경과 관찰, 의사가 권한 AREDS2 보충제, 습성 황반변성의 안구 내 주사 등이 사용됩니다.",
            urgent:"직선이 갑자기 휘어 보이거나 중심에 새로운 빈 점이 생기면 빠르게 안과에 연락하세요.",
            caption:"중기 연령관련 황반변성 안저 사진으로, 황반 주변의 드루젠이 밝은 점처럼 보입니다.",
            source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/age-related-macular-degeneration"
        },
        {
            t:"녹내장", d:"시신경이 손상되어 주로 주변 시야부터 서서히 줄어드는 질환군입니다.",
            detail:"녹내장은 하나의 병이 아니라 시신경을 손상시키는 여러 질환의 묶음입니다. 안압이 높은 경우가 많지만 정상 안압에서도 생길 수 있으며, 가장 흔한 개방각 녹내장은 초기 증상이 거의 없습니다.",
            symptoms:["초기에는 자각 증상이 없는 경우가 많음", "진행하면 주변 시야의 빈 곳과 시야 협착", "급성 폐쇄각에서는 심한 눈 통증·충혈·두통·메스꺼움·흐림"],
            risk:"고령, 가족력, 높은 안압, 특정 인종적 배경, 눈 외상 또는 장기간의 스테로이드 사용 등이 위험과 관련됩니다.",
            care:"안압만으로 판단하지 않고 산동검사, 시신경 평가와 시야검사를 함께 시행합니다. 안약, 레이저 또는 수술은 손상을 늦추지만 이미 잃은 시야를 되돌리지는 못합니다.",
            urgent:"심한 눈 통증과 충혈, 갑작스러운 흐림, 두통이나 메스꺼움이 함께 나타나면 급성 폐쇄각 가능성이 있어 즉시 응급 진료가 필요합니다.",
            caption:"급성 폐쇄각 녹내장의 임상 예시입니다. 흔한 개방각 녹내장은 겉으로 정상처럼 보일 수 있습니다.",
            source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/glaucoma"
        },
        {
            t:"당뇨망막병증", d:"당뇨로 망막의 미세혈관이 손상되어 출혈·부종과 시력 저하를 일으킬 수 있습니다.",
            detail:"높은 혈당에 장기간 노출되면 망막 혈관이 약해져 새거나 막힐 수 있습니다. 초기에는 증상이 없어도 진행할 수 있으며, 황반부종이나 신생혈관이 생기면 시력을 크게 위협할 수 있습니다.",
            symptoms:["초기에는 아무 증상이 없을 수 있음", "시야에 점이나 실오라기 같은 비문이 늘어남", "시야가 흐리거나 어두운 부분이 생기고 시력이 떨어짐"],
            risk:"당뇨를 앓은 기간, 혈당 조절 불량, 고혈압·고지혈증, 임신 등이 위험을 높일 수 있습니다.",
            care:"당뇨가 있다면 증상이 없어도 정기적인 산동 안저검사가 중요합니다. 혈당·혈압·지질 관리와 함께 단계에 따라 안구 내 주사, 레이저 또는 유리체 수술을 시행할 수 있습니다.",
            urgent:"비문이 갑자기 많아지거나 시야가 커튼처럼 가려지고 시력이 급격히 떨어지면 즉시 안과 진료를 받으세요.",
            caption:"초기 당뇨망막병증의 안저 사진으로, 미세혈관 변화는 사진에서 매우 작게 보일 수 있습니다.",
            source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/diabetic-retinopathy"
        }
    ],
    en: [
        {t:"Cataract", d:"Clouding of the eye’s lens can cause blurred vision and glare.", detail:"A cataract forms inside the eye when the normally clear lens becomes cloudy. It usually progresses slowly and may affect each eye differently.", symptoms:["Blurred, hazy, or double vision", "Glare, halos, and poorer night vision", "Faded colors or frequent prescription changes"], risk:"Risk rises with age and may also be increased by diabetes, smoking, long-term steroid use, previous eye injury, or surgery.", care:"A comprehensive dilated eye exam can confirm it. Lighting or prescription changes may help early on; surgery is considered when daily activities are affected.", urgent:"Sudden vision loss, severe pain, or marked redness is not typical of cataract and needs prompt eye care.", caption:"Clinical photograph of an advanced cataract with a gray-white cloudy lens.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/cataracts"},
        {t:"Age-related Macular Degeneration", d:"Damage to the macula can blur or distort central vision.", detail:"AMD affects the macula, which provides sharp straight-ahead vision. Dry and wet forms progress differently, and early disease may have no symptoms.", symptoms:["Straight lines look wavy or crooked", "A blurred, blank, or dark area in central vision", "More difficulty in dim light or reduced color brightness"], risk:"Age 55 or older, smoking, family history, high blood pressure, and high cholesterol are associated with higher risk.", care:"Dilated examination and OCT help identify the stage and type. Monitoring, clinician-recommended AREDS2 supplements, or anti-VEGF injections may be used depending on the diagnosis.", urgent:"New distortion or a new blank spot in central vision should be assessed promptly.", caption:"Fundus photograph of intermediate AMD showing bright drusen around the macula.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/age-related-macular-degeneration"},
        {t:"Glaucoma", d:"A group of diseases that damage the optic nerve, often reducing side vision first.", detail:"Glaucoma can occur with high or normal eye pressure. The common open-angle form often has no early symptoms, so an eye exam is needed to detect it.", symptoms:["Often no symptoms at first", "Blind spots or gradual loss of peripheral vision", "Acute angle closure may cause severe eye pain, redness, nausea, and blur"], risk:"Older age, family history, high eye pressure, some ethnic backgrounds, eye injury, and long-term steroid use may increase risk.", care:"Assessment includes the optic nerve, eye pressure, and visual field. Drops, laser treatment, or surgery can slow damage but cannot restore vision already lost.", urgent:"Severe eye pain with redness, sudden blur, headache, or nausea can be an emergency.", caption:"Clinical example of acute angle-closure glaucoma. Common open-angle glaucoma may look normal from the outside.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/glaucoma"},
        {t:"Diabetic Retinopathy", d:"Diabetes can damage retinal blood vessels and cause swelling, bleeding, and vision loss.", detail:"Long-term high blood sugar can weaken or block retinal vessels. Early disease may be silent, while macular edema or abnormal new vessels can threaten vision.", symptoms:["Often no symptoms in the early stages", "More floaters or spots in vision", "Blurred vision, dark areas, or vision loss"], risk:"Longer duration of diabetes, poor glucose control, high blood pressure, high cholesterol, and pregnancy can increase risk.", care:"Regular dilated eye exams are important even without symptoms. Glucose, blood pressure, and lipid control plus injections, laser, or surgery may be recommended by stage.", urgent:"A sudden shower of floaters, a curtain-like shadow, or rapid vision loss needs urgent assessment.", caption:"Fundus photograph of background diabetic retinopathy; early vessel changes can be subtle.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/diabetic-retinopathy"}
    ],
    es: [
        {t:"Cataratas", d:"La opacidad del cristalino puede causar visión borrosa y deslumbramiento.", detail:"La catarata aparece dentro del ojo cuando el cristalino transparente se vuelve opaco. Suele progresar lentamente y de forma distinta en cada ojo.", symptoms:["Visión borrosa, brumosa o doble", "Deslumbramiento, halos y peor visión nocturna", "Colores apagados o cambios frecuentes de graduación"], risk:"La edad, diabetes, tabaco, corticoides prolongados y lesiones o cirugías oculares pueden aumentar el riesgo.", care:"Se confirma con un examen ocular completo con dilatación. La cirugía se valora cuando limita la vida diaria.", urgent:"La pérdida súbita de visión, dolor intenso o enrojecimiento marcado requiere atención rápida.", caption:"Fotografía clínica de una catarata avanzada con cristalino gris-blanco.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/cataracts"},
        {t:"Degeneración Macular", d:"El daño de la mácula puede nublar o deformar la visión central.", detail:"La DMAE afecta la mácula, responsable de la visión central detallada. Las formas seca y húmeda evolucionan de modo diferente y al inicio puede no haber síntomas.", symptoms:["Líneas rectas onduladas", "Zona borrosa, vacía u oscura en el centro", "Más dificultad con poca luz"], risk:"Edad mayor de 55 años, tabaco, antecedentes familiares, hipertensión y colesterol alto.", care:"El fondo de ojo dilatado y la OCT ayudan a definir el tipo. Según la etapa se usa vigilancia, suplementos indicados por el médico o inyecciones anti-VEGF.", urgent:"Una nueva distorsión o mancha central debe valorarse pronto.", caption:"Fondo de ojo con DMAE intermedia y drusas claras alrededor de la mácula.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/age-related-macular-degeneration"},
        {t:"Glaucoma", d:"Grupo de enfermedades que dañan el nervio óptico y suelen reducir primero la visión lateral.", detail:"Puede aparecer con presión ocular alta o normal. El glaucoma de ángulo abierto suele no dar síntomas al inicio.", symptoms:["Frecuentemente sin síntomas iniciales", "Puntos ciegos o pérdida gradual de visión periférica", "El cierre angular agudo puede causar dolor, ojo rojo, náuseas y visión borrosa"], risk:"Edad, antecedentes familiares, presión ocular alta, lesión ocular y uso prolongado de corticoides.", care:"Se evalúan nervio óptico, presión y campo visual. Gotas, láser o cirugía pueden frenar el daño, pero no recuperar la visión perdida.", urgent:"Dolor ocular intenso con enrojecimiento, visión borrosa, cefalea o náuseas es una urgencia.", caption:"Ejemplo de glaucoma agudo por cierre angular; el glaucoma común puede parecer normal externamente.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/glaucoma"},
        {t:"Retinopatía Diabética", d:"La diabetes puede dañar los vasos de la retina y causar edema, hemorragia y pérdida visual.", detail:"La glucosa alta durante mucho tiempo debilita o bloquea los vasos de la retina. Las fases iniciales pueden no dar síntomas.", symptoms:["A menudo sin síntomas al inicio", "Más manchas o moscas volantes", "Visión borrosa, zonas oscuras o pérdida visual"], risk:"Duración de la diabetes, control deficiente, hipertensión, colesterol alto y embarazo.", care:"Son importantes los exámenes periódicos con dilatación. Según la etapa pueden indicarse control metabólico, inyecciones, láser o cirugía.", urgent:"Muchas moscas volantes nuevas, una sombra tipo cortina o pérdida rápida de visión requieren atención urgente.", caption:"Fondo de ojo con retinopatía diabética de fondo; los cambios iniciales pueden ser sutiles.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/diabetic-retinopathy"}
    ],
    fr: [
        {t:"Cataracte", d:"L’opacification du cristallin peut provoquer vision floue et éblouissement.", detail:"La cataracte se forme à l’intérieur de l’œil lorsque le cristallin transparent devient opaque. Elle évolue généralement lentement.", symptoms:["Vision floue, voilée ou double", "Éblouissement, halos et baisse de vision nocturne", "Couleurs ternes ou changements fréquents de correction"], risk:"Âge, diabète, tabac, corticoïdes prolongés, traumatisme ou chirurgie oculaire.", care:"Un examen complet avec dilatation confirme le diagnostic. La chirurgie est envisagée lorsque la vie quotidienne est gênée.", urgent:"Une baisse brutale de vision, une douleur intense ou une rougeur marquée nécessite une consultation rapide.", caption:"Photographie clinique d’une cataracte avancée avec cristallin gris-blanc.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/cataracts"},
        {t:"Dégénérescence Maculaire", d:"Une atteinte de la macula peut brouiller ou déformer la vision centrale.", detail:"La DMLA touche la macula, responsable de la vision centrale précise. Les formes sèche et humide évoluent différemment et le début peut être silencieux.", symptoms:["Lignes droites ondulées", "Zone floue, vide ou sombre au centre", "Difficulté accrue en faible lumière"], risk:"Âge supérieur à 55 ans, tabac, antécédents familiaux, hypertension et cholestérol élevé.", care:"Le fond d’œil dilaté et l’OCT précisent le type. Surveillance, compléments AREDS2 prescrits ou injections anti-VEGF peuvent être proposés selon le stade.", urgent:"Toute nouvelle déformation ou tache centrale doit être évaluée rapidement.", caption:"Fond d’œil avec DMLA intermédiaire et drusen clairs autour de la macula.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/age-related-macular-degeneration"},
        {t:"Glaucome", d:"Groupe de maladies lésant le nerf optique, souvent d’abord la vision périphérique.", detail:"Le glaucome peut survenir avec une pression oculaire élevée ou normale. La forme à angle ouvert est souvent silencieuse au début.", symptoms:["Souvent aucun symptôme initial", "Taches aveugles ou perte progressive du champ périphérique", "La fermeture aiguë peut provoquer douleur, rougeur, nausées et flou"], risk:"Âge, antécédents familiaux, pression élevée, traumatisme oculaire et corticoïdes prolongés.", care:"L’évaluation associe nerf optique, pression et champ visuel. Collyres, laser ou chirurgie ralentissent les lésions sans restaurer la vision perdue.", urgent:"Douleur intense avec œil rouge, flou soudain, céphalée ou nausées constitue une urgence.", caption:"Exemple de fermeture aiguë de l’angle ; le glaucome courant peut paraître normal extérieurement.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/glaucoma"},
        {t:"Rétinopathie Diabétique", d:"Le diabète peut léser les vaisseaux rétiniens et entraîner œdème, saignement et baisse visuelle.", detail:"Une glycémie élevée prolongée fragilise ou obstrue les vaisseaux de la rétine. Les premiers stades peuvent rester sans symptômes.", symptoms:["Souvent aucun symptôme au début", "Augmentation des corps flottants", "Vision floue, zones sombres ou perte de vision"], risk:"Durée du diabète, contrôle insuffisant, hypertension, cholestérol élevé et grossesse.", care:"Des examens réguliers avec dilatation sont essentiels. Selon le stade : contrôle métabolique, injections, laser ou chirurgie.", urgent:"Une pluie soudaine de corps flottants, un voile ou une baisse rapide de vision nécessite une consultation urgente.", caption:"Fond d’œil avec rétinopathie diabétique débutante ; les changements peuvent être discrets.", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/diabetic-retinopathy"}
    ],
    ja: [
        {t:"白内障", d:"水晶体の濁りにより、かすみやまぶしさが生じます。", detail:"白内障は目の中の透明な水晶体が徐々に濁る病気です。多くはゆっくり進み、左右で進行が異なることがあります。", symptoms:["かすむ・ぼやける・二重に見える", "まぶしさ、光の輪、夜間視力の低下", "色が薄く見える、度数が頻繁に変わる"], risk:"加齢、糖尿病、喫煙、長期のステロイド使用、眼外傷や手術歴など。", care:"散瞳を含む総合眼科検査で確認します。生活への支障が大きくなると手術を検討します。", urgent:"急な視力低下、強い痛みや充血は典型的ではないため、早めに受診してください。", caption:"進行した白内障で水晶体が灰白色に濁って見える臨床写真です。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/cataracts"},
        {t:"加齢黄斑変性", d:"黄斑の障害により中心視野がぼやけたり歪んだりします。", detail:"加齢黄斑変性は、正面を細かく見る黄斑に生じます。萎縮型と滲出型があり、初期には無症状のことがあります。", symptoms:["直線が波打って見える", "中心にぼやけ・空白・暗点がある", "暗い場所で見えにくく色が薄く感じる"], risk:"55歳以上、喫煙、家族歴、高血圧・高コレステロールなど。", care:"散瞳眼底検査やOCTで型と段階を確認し、経過観察、医師が勧めるAREDS2、抗VEGF注射などを選択します。", urgent:"新しい歪みや中心の空白が出たら早めに眼科へ連絡してください。", caption:"中期の加齢黄斑変性の眼底写真で、黄斑周囲に明るいドルーゼンが見えます。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/age-related-macular-degeneration"},
        {t:"緑内障", d:"視神経が損傷し、主に周辺視野から徐々に失われる病気の総称です。", detail:"緑内障は眼圧が高くても正常でも起こります。最も多い開放隅角緑内障は初期症状がほとんどありません。", symptoms:["初期は無症状が多い", "周辺視野の欠けや視野狭窄", "急性閉塞隅角では強い痛み、充血、吐き気、かすみ"], risk:"高齢、家族歴、高眼圧、眼外傷、長期のステロイド使用など。", care:"眼圧だけでなく視神経と視野を検査します。点眼、レーザー、手術は進行を遅らせますが失った視野は戻せません。", urgent:"強い眼痛と充血、急なかすみ、頭痛や吐き気は救急受診が必要です。", caption:"急性閉塞隅角緑内障の例です。一般的な開放隅角緑内障は外見が正常なことがあります。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/glaucoma"},
        {t:"糖尿病網膜症", d:"糖尿病により網膜血管が傷み、浮腫・出血・視力低下を起こすことがあります。", detail:"高血糖が長く続くと網膜血管が弱くなったり詰まったりします。初期は無症状でも進行することがあります。", symptoms:["初期は無症状のことが多い", "飛蚊症や点が増える", "かすみ、暗い部分、視力低下"], risk:"糖尿病の罹病期間、血糖管理不良、高血圧・高脂血症、妊娠など。", care:"症状がなくても定期的な散瞳眼底検査が重要です。段階により代謝管理、注射、レーザー、手術を行います。", urgent:"飛蚊症が急に増える、カーテン状の影、急な視力低下はすぐに受診してください。", caption:"初期の糖尿病網膜症の眼底写真で、微細な血管変化は目立たないことがあります。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/diabetic-retinopathy"}
    ],
    zh: [
        {t:"白内障", d:"晶状体混浊可引起视物模糊和眩光。", detail:"白内障发生在眼内透明晶状体逐渐混浊时，通常进展缓慢，双眼程度可不同。", symptoms:["视物模糊、雾状或重影", "眩光、光晕和夜间视力下降", "颜色变淡或眼镜度数频繁变化"], risk:"年龄、糖尿病、吸烟、长期使用激素、眼外伤或手术史。", care:"通过散瞳综合眼科检查确认。影响日常生活时由眼科医生评估手术。", urgent:"突然视力下降、剧烈眼痛或明显充血并非典型白内障表现，应尽快就医。", caption:"进展期白内障的临床照片，可见晶状体呈灰白色混浊。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/cataracts"},
        {t:"年龄相关性黄斑变性", d:"黄斑受损可导致中心视力模糊或变形。", detail:"该病累及负责精细中心视力的黄斑，分干性和湿性，早期可能没有症状。", symptoms:["直线看起来弯曲或波浪状", "中心出现模糊、空白或暗点", "暗处视物更困难、颜色变淡"], risk:"55岁以上、吸烟、家族史、高血压和高胆固醇。", care:"散瞳眼底检查和OCT用于判断类型与阶段，可根据情况观察、使用医生建议的AREDS2或抗VEGF注射。", urgent:"新出现的视物变形或中心空白应尽快检查。", caption:"中期年龄相关性黄斑变性的眼底照片，黄斑周围可见亮色玻璃膜疣。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/age-related-macular-degeneration"},
        {t:"青光眼", d:"一组损伤视神经、常先影响周边视野的疾病。", detail:"青光眼可发生于高眼压或正常眼压。常见的开角型早期通常没有症状。", symptoms:["早期常无症状", "周边视野盲点或逐渐缩窄", "急性闭角可出现剧烈眼痛、充血、恶心和视物模糊"], risk:"年龄、家族史、高眼压、眼外伤和长期使用激素等。", care:"需综合评估视神经、眼压和视野。滴眼液、激光或手术可减慢损伤，但不能恢复已丢失的视野。", urgent:"剧烈眼痛伴充血、突然模糊、头痛或恶心属于急症。", caption:"急性闭角型青光眼临床示例；常见开角型外观可能正常。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/glaucoma"},
        {t:"糖尿病视网膜病变", d:"糖尿病可损伤视网膜血管，引起水肿、出血和视力下降。", detail:"长期高血糖可使视网膜血管变弱或堵塞，早期即使没有症状也可能进展。", symptoms:["早期常无症状", "飞蚊或黑点增多", "视物模糊、暗区或视力下降"], risk:"糖尿病病程、血糖控制不佳、高血压、高血脂和妊娠。", care:"即使无症状也应定期散瞳眼底检查，并管理血糖、血压和血脂；按阶段可采用注射、激光或手术。", urgent:"飞蚊突然大量增加、幕帘样阴影或视力迅速下降需紧急就医。", caption:"背景期糖尿病视网膜病变的眼底照片，早期血管变化可能很细微。", source:"https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/diabetic-retinopathy"}
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
    vt_result_title: "기능검사 결과", vt_redo: "다시 검사", vt_recalibrate: "화면 다시 맞추기",
    vt_need_calib: "먼저 화면 크기 맞추기를 완료해주세요.",
    vt_asym: "좌우 결과 차이가 관찰됐습니다. 측정 조건에 따라 달라질 수 있으므로 재검사 후에도 차이가 지속되면 안과에서 확인하세요.",
    vt_unmeasurable: "한쪽 눈의 측정이 완료되지 않았습니다. 조건을 확인해 재검사하고, 차이가 지속되면 안과에서 확인하세요.",
    vt_unmeasurable_both: "양쪽 눈 모두 측정이 완료되지 않았습니다. 조명·거리·눈 가림을 확인하고 다시 검사해 주세요.",
    q_age: "연령대를 알려주세요.", q_diabetes: "당뇨가 있으신가요?",
    q_hypertension: "고혈압이 있으신가요?", q_family: "가족 중 녹내장·황반변성 진단을 받은 분이 있나요?",
    q_smoking: "현재 흡연 중이신가요?",
    age_under40: "40세 미만", age_40s: "40–49세", age_50s: "50–59세", age_60s: "60–69세", age_70plus: "70세 이상",
    risk_diabetes: "당뇨", risk_hypertension: "고혈압", risk_family: "가족력", risk_smoking: "흡연",
    tri_title: "권장 조치", tri_now: "빠른 시일 내 안과 진료를 권합니다",
    tri_weeks: "수 주 내 안과 검진을 권합니다", tri_monitor: "정기 검진으로 경과를 관찰하세요",
    tri_now_why: "사진 분석 또는 암슬러 검사에서 확인이 필요한 소견이 있었습니다.",
    tri_weeks_why: "경계 소견 또는 확인이 필요한 증상이 있었습니다.",
    tri_monitor_why: "이번 선별검사에서 빠른 확인을 권할 신호는 없었습니다. 정기 검진을 대신하지는 않습니다.",
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
    vt_result_title: "Functional test results", vt_redo: "Test again", vt_recalibrate: "Recalibrate screen",
    vt_need_calib: "Please complete screen calibration first.",
    vt_asym: "A difference between the two eyes was observed. Testing conditions can affect the result; repeat the test and seek an eye exam if the difference persists.",
    vt_unmeasurable: "The measurement could not be completed for one eye. Check the conditions and repeat the test; seek an eye exam if the difference persists.",
    vt_unmeasurable_both: "The measurement could not be completed for either eye. Check the lighting, distance and eye covering, then try again.",
    q_age: "What is your age range?", q_diabetes: "Do you have diabetes?",
    q_hypertension: "Do you have high blood pressure?", q_family: "Has a family member been diagnosed with glaucoma or macular degeneration?",
    q_smoking: "Do you currently smoke?",
    age_under40: "Under 40", age_40s: "40–49", age_50s: "50–59", age_60s: "60–69", age_70plus: "70+",
    risk_diabetes: "Diabetes", risk_hypertension: "Hypertension", risk_family: "Family history", risk_smoking: "Smoking",
    tri_title: "Recommended action", tri_now: "See an ophthalmologist soon",
    tri_weeks: "Schedule an eye exam within a few weeks", tri_monitor: "Monitor with routine check-ups",
    tri_now_why: "The photo analysis or Amsler test showed a finding that should be checked.",
    tri_weeks_why: "A borderline finding or a symptom that should be checked was reported.",
    tri_monitor_why: "This screening did not show a signal requiring prompt review. It does not replace routine eye exams.",
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
    vt_result_title: "Resultados funcionales", vt_redo: "Repetir test", vt_recalibrate: "Recalibrar pantalla",
    vt_need_calib: "Complete primero la calibración de pantalla.",
    vt_asym: "Se observó una diferencia entre ambos ojos. Las condiciones pueden afectar el resultado; repita la prueba y consulte si la diferencia persiste.",
    vt_unmeasurable: "No se pudo completar la medición de un ojo. Revise las condiciones, repita la prueba y consulte si la diferencia persiste.",
    vt_unmeasurable_both: "No se pudo completar la medición de ninguno de los ojos. Revise la luz, la distancia y la oclusión, y repita la prueba.",
    q_age: "¿Cuál es su rango de edad?", q_diabetes: "¿Tiene diabetes?",
    q_hypertension: "¿Tiene hipertensión?", q_family: "¿Algún familiar fue diagnosticado con glaucoma o degeneración macular?",
    q_smoking: "¿Fuma actualmente?",
    age_under40: "Menos de 40", age_40s: "40–49", age_50s: "50–59", age_60s: "60–69", age_70plus: "70+",
    risk_diabetes: "Diabetes", risk_hypertension: "Hipertensión", risk_family: "Antecedentes familiares", risk_smoking: "Tabaquismo",
    tri_title: "Acción recomendada", tri_now: "Consulte a un oftalmólogo pronto",
    tri_weeks: "Programe un examen ocular en unas semanas", tri_monitor: "Controle con revisiones periódicas",
    tri_now_why: "El análisis fotográfico o la prueba de Amsler mostró un hallazgo que conviene revisar.",
    tri_weeks_why: "Se registró un hallazgo límite o un síntoma que conviene revisar.",
    tri_monitor_why: "Este cribado no mostró señales que requieran revisión pronta. No sustituye los controles oculares habituales.",
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
    vt_result_title: "Résultats fonctionnels", vt_redo: "Refaire le test", vt_recalibrate: "Recalibrer l'écran",
    vt_need_calib: "Veuillez d'abord calibrer l'écran.",
    vt_asym: "Un écart entre les deux yeux a été observé. Les conditions peuvent influencer le résultat ; recommencez et consultez si l'écart persiste.",
    vt_unmeasurable: "La mesure n'a pas pu être terminée pour un œil. Vérifiez les conditions, recommencez et consultez si l'écart persiste.",
    vt_unmeasurable_both: "La mesure n'a pu être terminée pour aucun des deux yeux. Vérifiez l'éclairage, la distance et l'occlusion, puis recommencez.",
    q_age: "Quelle est votre tranche d'âge ?", q_diabetes: "Êtes-vous diabétique ?",
    q_hypertension: "Avez-vous de l'hypertension ?", q_family: "Un proche a-t-il été diagnostiqué d'un glaucome ou d'une DMLA ?",
    q_smoking: "Fumez-vous actuellement ?",
    age_under40: "Moins de 40", age_40s: "40–49", age_50s: "50–59", age_60s: "60–69", age_70plus: "70+",
    risk_diabetes: "Diabète", risk_hypertension: "Hypertension", risk_family: "Antécédents familiaux", risk_smoking: "Tabagisme",
    tri_title: "Action recommandée", tri_now: "Consultez un ophtalmologiste rapidement",
    tri_weeks: "Planifiez un examen dans quelques semaines", tri_monitor: "Surveillez lors des contrôles réguliers",
    tri_now_why: "L'analyse photo ou le test d'Amsler a montré un résultat qui doit être contrôlé.",
    tri_weeks_why: "Un résultat limite ou un symptôme à contrôler a été signalé.",
    tri_monitor_why: "Ce dépistage n'a pas montré de signal nécessitant un contrôle rapide. Il ne remplace pas les examens réguliers.",
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
    vt_result_title: "機能検査の結果", vt_redo: "もう一度検査", vt_recalibrate: "画面を再調整",
    vt_need_calib: "先に画面サイズの調整を完了してください。",
    vt_asym: "左右の結果に差が見られました。測定条件で変わることがあるため、再検査後も差が続く場合は眼科でご確認ください。",
    vt_unmeasurable: "片眼の測定を完了できませんでした。条件を確認して再検査し、差が続く場合は眼科でご確認ください。",
    vt_unmeasurable_both: "両眼とも測定を完了できませんでした。照明・距離・眼の遮蔽を確認して再度お試しください。",
    q_age: "年代を教えてください。", q_diabetes: "糖尿病はありますか？",
    q_hypertension: "高血圧はありますか？", q_family: "ご家族に緑内障・黄斑変性と診断された方はいますか？",
    q_smoking: "現在喫煙していますか？",
    age_under40: "40歳未満", age_40s: "40–49歳", age_50s: "50–59歳", age_60s: "60–69歳", age_70plus: "70歳以上",
    risk_diabetes: "糖尿病", risk_hypertension: "高血圧", risk_family: "家族歴", risk_smoking: "喫煙",
    tri_title: "推奨される対応", tri_now: "早めに眼科を受診してください",
    tri_weeks: "数週間以内に眼科検診を受けてください", tri_monitor: "定期検診で経過を観察してください",
    tri_now_why: "写真解析またはアムスラー検査で確認が必要な所見がありました。",
    tri_weeks_why: "境界所見または確認が必要な症状が報告されました。",
    tri_monitor_why: "今回のスクリーニングで早期確認を要する信号は見られませんでした。定期検診の代わりにはなりません。",
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
    vt_result_title: "功能检查结果", vt_redo: "重新检查", vt_recalibrate: "重新校准屏幕",
    vt_need_calib: "请先完成屏幕校准。",
    vt_asym: "双眼结果存在差异。测量条件可能影响结果；请重新检查，若差异持续请到眼科确认。",
    vt_unmeasurable: "一只眼的测量未能完成。请检查测量条件并重试；若差异持续请到眼科确认。",
    vt_unmeasurable_both: "双眼的测量均未能完成。请检查光线、距离和遮眼方式后重试。",
    q_age: "请问您的年龄段？", q_diabetes: "您有糖尿病吗？",
    q_hypertension: "您有高血压吗？", q_family: "家人中有被诊断为青光眼或黄斑变性的吗？",
    q_smoking: "您目前吸烟吗？",
    age_under40: "40岁以下", age_40s: "40–49岁", age_50s: "50–59岁", age_60s: "60–69岁", age_70plus: "70岁以上",
    risk_diabetes: "糖尿病", risk_hypertension: "高血压", risk_family: "家族史", risk_smoking: "吸烟",
    tri_title: "建议措施", tri_now: "建议尽快就诊眼科",
    tri_weeks: "建议数周内进行眼科检查", tri_monitor: "通过定期检查观察",
    tri_now_why: "照片分析或阿姆斯勒检查显示了需要确认的结果。",
    tri_weeks_why: "出现了临界结果或需要确认的症状。",
    tri_monitor_why: "本次筛查未显示需要尽快确认的信号，但不能替代定期眼科检查。",
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
  vt_lock_off: "화면 고정하기", vt_lock_on: "고정됨 — 해제하려면 탭",
  vt_lock_hint: "카드를 올려놓을 위치까지 스크롤한 뒤 <b>화면 고정</b>을 누르세요. 고정하면 카드가 닿아도 화면이 움직이지 않고, <b>+/−</b> 버튼으로만 크기를 바꿉니다.",
  vt_dist_tolerance: "거리가 10% 틀려도 시력 오차는 0.04 logMAR — <b>시력표 반 줄도 안 됩니다</b>. 대비감도는 이보다도 둔감하고, 좌우 눈 비교는 거리와 아예 무관합니다.",
  vt_dist_custom: "직접 입력 (cm)"
});
Object.assign(translations.en, {
  vt_lock_off: "Lock the screen", vt_lock_on: "Locked — tap to unlock",
  vt_lock_hint: "Scroll to where you want to rest the card, then tap <b>Lock the screen</b>. While locked, the card touching the screen won't move it — resize with the <b>+/−</b> buttons only.",
  vt_dist_tolerance: "A 10% distance error shifts acuity by only 0.04 logMAR — <b>less than half a line</b> on an eye chart. Contrast sensitivity is even less sensitive, and left/right comparison doesn't depend on distance at all.",
  vt_dist_custom: "Enter manually (cm)"
});
Object.assign(translations.es, {
  vt_lock_off: "Bloquear pantalla", vt_lock_on: "Bloqueada — toque para desbloquear",
  vt_lock_hint: "Desplácese hasta donde apoyará la tarjeta y pulse <b>Bloquear pantalla</b>. Bloqueada, la tarjeta no moverá la pantalla; ajuste solo con <b>+/−</b>.",
  vt_dist_tolerance: "Un error del 10% en distancia cambia la agudeza solo 0,04 logMAR — <b>menos de media línea</b>. La sensibilidad al contraste es aún menos sensible.",
  vt_dist_custom: "Introducir (cm)"
});
Object.assign(translations.fr, {
  vt_lock_off: "Verrouiller l'écran", vt_lock_on: "Verrouillé — touchez pour déverrouiller",
  vt_lock_hint: "Faites défiler jusqu'à l'endroit où poser la carte, puis touchez <b>Verrouiller l'écran</b>. Une fois verrouillé, la carte ne fera plus bouger l'écran ; ajustez avec <b>+/−</b>.",
  vt_dist_tolerance: "Une erreur de 10% sur la distance ne décale l'acuité que de 0,04 logMAR — <b>moins d'une demi-ligne</b>. La sensibilité au contraste y est encore moins sensible.",
  vt_dist_custom: "Saisir (cm)"
});
Object.assign(translations.ja, {
  vt_lock_off: "画面を固定", vt_lock_on: "固定中 — タップで解除",
  vt_lock_hint: "カードを置きたい位置までスクロールしてから<b>画面を固定</b>を押してください。固定中はカードが触れても画面が動かず、<b>+/−</b>ボタンだけでサイズを変えます。",
  vt_dist_tolerance: "距離が10%ずれても視力の誤差は0.04 logMAR — <b>視力表の半行未満</b>です。コントラスト感度はさらに鈍感で、左右比較は距離と無関係です。",
  vt_dist_custom: "直接入力 (cm)"
});
Object.assign(translations.zh, {
  vt_lock_off: "锁定屏幕", vt_lock_on: "已锁定 — 点击解锁",
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
  find_vt_ok: "측정이 완료된 기능검사 항목에서는 좌우 눈의 뚜렷한 차이가 관찰되지 않았습니다(참고용 측정).",
  find_vt_unmeasurable: "한쪽 눈은 가장 큰 시표도 판별하지 못했습니다. 측정 조건 문제일 수도 있으나, 좌우 차이가 클 가능성이 있어 안과 확인을 권합니다.",
  find_vt_unmeasurable_both: "양쪽 눈 모두 기능검사 측정이 완료되지 않아 좌우를 비교할 수 없습니다. 조명·거리·눈 가림을 확인하고 다시 검사해 주세요.",
  vt_cross_match: "사진 분석에서도 좌우 차이 소견이 있었습니다(두 결과 모두 참고용입니다).",
  tri_factors: "정기 검진을 권하는 이유: {items}",
  save_saving: "저장 중...", save_done: "저장했습니다.",
  save_failed: "저장하지 못했습니다. 결과는 화면에서 계속 보실 수 있습니다.", save_retry: "다시 시도",
  calib_stale: "화면 설정이 바뀐 것 같습니다(회전·확대·창 크기). 정확한 측정을 위해 다시 보정해 주세요."
});
Object.assign(translations.en, {
  vt_intro_desc: "Uses on-screen optotypes to look at the difference between your two eyes, for reference only. It does not provide a clinical acuity value or a diagnosis.",
  vt_beta_note: "Reference measurement. Values vary with device, lighting and distance, so use it to compare your two eyes rather than as an absolute number.",
  find_vt_asym: "A difference between your eyes was observed in the functional test. This is a reference measurement, but if the difference persists, have it checked at a clinic.",
  find_vt_ok: "No marked difference between your eyes was observed in the functional-test items that were completed (reference measurement).",
  find_vt_unmeasurable: "One eye could not identify even the largest optotype. This may be a testing-condition issue, but the difference between your eyes may be large, so an eye exam is recommended.",
  find_vt_unmeasurable_both: "The functional measurement could not be completed for either eye, so the two eyes cannot be compared. Check the lighting, distance and eye covering, then try again.",
  vt_cross_match: "The photo analysis also showed a side difference (both are reference findings).",
  tri_factors: "Why regular check-ups are recommended: {items}",
  save_saving: "Saving...", save_done: "Saved.",
  save_failed: "Could not save. Your results remain visible on screen.", save_retry: "Try again",
  calib_stale: "Your display settings seem to have changed (rotation, zoom, window size). Please calibrate again for an accurate measurement."
});
Object.assign(translations.es, {
  vt_intro_desc: "Usa optotipos en pantalla para observar la diferencia entre sus dos ojos, solo como referencia. No ofrece agudeza clínica ni diagnóstico.",
  vt_beta_note: "Medición de referencia. Los valores varían según dispositivo, luz y distancia; úselo para comparar ambos ojos, no como valor absoluto.",
  find_vt_asym: "Se observó una diferencia entre ojos en la prueba funcional. Es una medición de referencia, pero si persiste conviene revisarla.",
  find_vt_ok: "No se observó una diferencia marcada en los apartados completados de la prueba funcional (medición de referencia).",
  find_vt_unmeasurable: "Un ojo no identificó ni el optotipo más grande. Puede deberse a las condiciones, pero la diferencia podría ser grande; se recomienda examen.",
  find_vt_unmeasurable_both: "No se pudo completar la medición funcional de ninguno de los ojos, por lo que no pueden compararse. Revise la luz, la distancia y la oclusión, y repita la prueba.",
  vt_cross_match: "El análisis de foto también mostró diferencia lateral (ambos son hallazgos de referencia).",
  tri_factors: "Por qué se recomiendan revisiones periódicas: {items}",
  save_saving: "Guardando...", save_done: "Guardado.",
  save_failed: "No se pudo guardar. Sus resultados siguen visibles en pantalla.", save_retry: "Reintentar",
  calib_stale: "Parece que cambió la configuración de pantalla (rotación, zoom, tamaño). Calibre de nuevo."
});
Object.assign(translations.fr, {
  vt_intro_desc: "Utilise des optotypes à l'écran pour observer l'écart entre vos deux yeux, à titre indicatif. Ne fournit ni acuité clinique ni diagnostic.",
  vt_beta_note: "Mesure indicative. Les valeurs varient selon l'appareil, l'éclairage et la distance ; utilisez-la pour comparer les deux yeux.",
  find_vt_asym: "Un écart entre les yeux a été observé au test fonctionnel. Mesure indicative, mais s'il persiste, faites-le vérifier.",
  find_vt_ok: "Aucun écart marqué n'a été observé dans les éléments terminés du test fonctionnel (mesure indicative).",
  find_vt_unmeasurable: "Un œil n'a pas identifié même le plus grand optotype. Cela peut venir des conditions, mais l'écart pourrait être important ; un examen est recommandé.",
  find_vt_unmeasurable_both: "La mesure fonctionnelle n'a pu être terminée pour aucun des deux yeux ; ils ne peuvent donc pas être comparés. Vérifiez les conditions et recommencez.",
  vt_cross_match: "L'analyse photo montrait aussi une différence latérale (les deux sont indicatifs).",
  tri_factors: "Pourquoi des contrôles réguliers sont recommandés : {items}",
  save_saving: "Enregistrement...", save_done: "Enregistré.",
  save_failed: "Enregistrement impossible. Vos résultats restent affichés.", save_retry: "Réessayer",
  calib_stale: "Vos réglages d'affichage semblent avoir changé (rotation, zoom, taille). Veuillez recalibrer."
});
Object.assign(translations.ja, {
  vt_intro_desc: "画面に表示した視標で左右の差を参考として確認します。臨床的な視力値や診断は提供しません。",
  vt_beta_note: "参考測定です。機器・照明・距離で値が変わるため、絶対値ではなく左右差を見る用途にお使いください。",
  find_vt_asym: "機能検査で左右差が観察されました。参考測定ですが、差が続く場合は眼科で確認してください。",
  find_vt_ok: "測定を完了した機能検査項目では、左右の明らかな差は観察されませんでした（参考測定）。",
  find_vt_unmeasurable: "片方の目は最大の視標も判別できませんでした。測定条件の問題の可能性もありますが、左右差が大きい可能性があり受診をお勧めします。",
  find_vt_unmeasurable_both: "両眼とも機能検査の測定が完了せず、左右を比較できません。照明・距離・眼の遮蔽を確認して再度お試しください。",
  vt_cross_match: "写真解析でも左右差の所見がありました（いずれも参考情報です）。",
  tri_factors: "定期検診をお勧めする理由: {items}",
  save_saving: "保存中...", save_done: "保存しました。",
  save_failed: "保存できませんでした。結果は画面で引き続きご確認いただけます。", save_retry: "再試行",
  calib_stale: "画面設定が変わったようです（回転・ズーム・サイズ）。正確な測定のため再調整してください。"
});
Object.assign(translations.zh, {
  vt_intro_desc: "用屏幕上的视标以参考方式观察双眼差异。不提供临床视力值或诊断。",
  vt_beta_note: "参考性测量。数值会随设备、光线与距离变化，请用于比较双眼而非作为绝对值。",
  find_vt_asym: "功能检查中观察到双眼差异。这是参考性测量，若差异持续请到眼科确认。",
  find_vt_ok: "在已完成的功能检查项目中，未观察到双眼明显差异（参考性测量）。",
  find_vt_unmeasurable: "一只眼连最大的视标也无法辨认。可能与测量条件有关，但双眼差异可能较大，建议就诊。",
  find_vt_unmeasurable_both: "双眼的功能检查测量均未能完成，因此无法比较。请检查光线、距离和遮眼方式后重试。",
  vt_cross_match: "照片分析也显示了单侧差异（两者均为参考信息）。",
  tri_factors: "建议定期检查的原因：{items}",
  save_saving: "保存中...", save_done: "已保存。",
  save_failed: "未能保存。结果仍会显示在屏幕上。", save_retry: "重试",
  calib_stale: "屏幕设置似乎已更改（旋转、缩放、窗口大小）。请重新校准以确保测量准确。"
});
