// Local preview only. No photo is sent until the user checks the visible eye.
const photoReviewCopy = {
    ko: ['사진에서 눈동자가 보이나요?', '눈을 뜬 상태에서 홍채와 동공이 또렷하게 보여야 합니다. 감은 눈, 안경 반사, 흐린 사진은 다시 골라주세요. 자동 검사는 감은 눈을 놓칠 수 있습니다.', '눈동자가 보여요 · 분석하기', '다른 사진 고르기', '사진이 너무 어두워 판독할 수 없어요. 플래시를 끄고 고른 밝은 조명에서 다시 찍어주세요.'],
    en: ['Can you see the iris and pupil?', 'Check that the eye is open and the iris and pupil are clearly visible. Choose another photo if eyes are closed, blurred or obscured by glasses. Automatic checks may miss closed eyes.', 'They are visible · Analyze', 'Choose another photo', 'The photo is too dark to assess. Retake it in even, bright light with the flash off.'],
    es: ['¿Se ven el iris y la pupila?', 'Compruebe que el ojo esté abierto y el iris y la pupila sean visibles. Cambie la foto si está borrosa, con ojos cerrados o reflejos de gafas. El control automático puede no detectar ojos cerrados.', 'Se ven · Analizar', 'Elegir otra foto', 'La foto es demasiado oscura. Repítala con luz uniforme y brillante, sin flash.'],
    fr: ['Voyez-vous l’iris et la pupille ?', 'Vérifiez que l’œil est ouvert et que l’iris et la pupille sont visibles. Changez de photo si elle est floue, si les yeux sont fermés ou masqués par des reflets. Le contrôle automatique peut manquer les yeux fermés.', 'Ils sont visibles · Analyser', 'Choisir une autre photo', 'La photo est trop sombre. Reprenez-la sous un éclairage clair et uniforme, sans flash.'],
    ja: ['虹彩と瞳孔が見えますか？', '目を開けた状態で虹彩と瞳孔がはっきり見えるか確認してください。閉じた目、眼鏡の反射、ぼやけた写真は選び直してください。自動チェックは閉じた目を見逃すことがあります。', '見えます・分析する', '別の写真を選ぶ', '写真が暗すぎます。フラッシュを切り、均一で明るい場所で撮り直してください。'],
    zh: ['能看清虹膜和瞳孔吗？', '请确认眼睛睁开，虹膜和瞳孔清晰可见。如果闭眼、模糊或有眼镜反光，请重新选图。自动检查可能无法识别闭眼。', '看得清 · 开始分析', '选择其他照片', '照片太暗，无法评估。请关闭闪光灯，在明亮且均匀的光线下重新拍摄。']
};
for (const [lang, copy] of Object.entries(photoReviewCopy)) {
    ['review_title','review_body','review_confirm','review_retake','ai_dark'].forEach((key, i) => translations[lang][key] = copy[i]);
}
let _photoReview = null;
function cancelPhotoReview() { if (_photoReview) _photoReview(false); }
function reviewPhoto(file) {
    cancelPhotoReview();
    const dialog = document.getElementById('photo-review');
    if (!dialog || typeof dialog.showModal !== 'function') return Promise.resolve(false);
    return new Promise(resolve => {
        const preview = document.getElementById('photo-review-image');
        const confirm = document.getElementById('photo-review-confirm');
        const retake = document.getElementById('photo-review-retake');
        const url = URL.createObjectURL(file);
        const finish = accepted => {
            if (_photoReview !== finish) return;
            _photoReview = null;
            preview.onload = preview.onerror = null;
            preview.removeAttribute('src'); URL.revokeObjectURL(url);
            dialog.close(); resolve(accepted);
        };
        _photoReview = finish;
        confirm.disabled = true;
        preview.onload = () => { if (_photoReview === finish) confirm.disabled = false; };
        preview.onerror = () => {
            finish(false);
            showUploadError(uploadErrorMessage({code:'IMAGE_INVALID'}));
        };
        confirm.onclick = () => { if (!confirm.disabled) finish(true); };
        retake.onclick = () => finish(false);
        const symptoms = document.getElementById('photo-review-symptoms');
        if (symptoms) symptoms.onclick = () => { finish(false); startSymptomCheck(); };
        dialog.oncancel = event => { event.preventDefault(); finish(false); };
        preview.src = url;
        dialog.showModal();
        retake.focus();
    });
}
