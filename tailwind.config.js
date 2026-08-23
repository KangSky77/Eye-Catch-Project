/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./static/index.html", "./static/app-*.js"],
  theme: {
    extend: {
      // 디자인 토큰을 여기에 둡니다.
      // style.css에서 .bg-blue-600 / .rounded-2xl 같은 유틸리티 클래스명을
      // !important로 재정의하면, 이후 그 클래스를 쓰는 모든 코드가 조용히 다른 값을
      // 갖게 되고 되돌릴 방법도 없습니다. 스케일 값 자체를 바꾸는 건 config가 제자리입니다.
      colors: {
        blue:  { 600: '#155eef' },   // --ec-blue  (기본 #2563eb 대체)
        slate: { 900: '#0b1f3a' },   // --ec-navy  (기본 #0f172a 대체)
      },
      borderRadius: {
        '2xl': '12px',               // 카드/버튼 공통 반경 (기본 1rem 대체)
      },
    },
  },
  plugins: [],
};
