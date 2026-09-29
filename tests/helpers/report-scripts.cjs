const fs = require('node:fs');
const path = require('node:path');

const REPORT_SCRIPTS = ['app-report.js', 'app-report-chat.js', 'app-report-pdf.js'];
function readReportScripts() {
    return REPORT_SCRIPTS.map(file => fs.readFileSync(path.join(__dirname, '../../static', file), 'utf8')).join('\n');
}
module.exports = { REPORT_SCRIPTS, readReportScripts };
