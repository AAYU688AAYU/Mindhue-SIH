import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ICDR Staging Evaluation Helpers
const ICDR_STAGES = {
  0: { label: 'No Apparent DR', referable: false, urgency: 'ROUTINE' },
  1: { label: 'Mild NPDR', referable: false, urgency: 'ROUTINE' },
  2: { label: 'Moderate NPDR', referable: true, urgency: 'PRIORITY' },
  3: { label: 'Severe NPDR', referable: true, urgency: 'URGENT' },
  4: { label: 'Proliferative DR', referable: true, urgency: 'EMERGENCY' }
};

function classifyReferableDR(icdrGrade) {
  return icdrGrade >= 2;
}

function determineClinicalUrgency(icdrGrade, macularEdemaRisk = false) {
  if (icdrGrade === 4) return 'EMERGENCY';
  if (icdrGrade === 3 || macularEdemaRisk) return 'URGENT';
  if (icdrGrade === 2) return 'PRIORITY';
  return 'ROUTINE';
}

function evaluateIQAQuality(iqaScore) {
  return iqaScore >= 70.0 ? 'GRADEABLE' : 'UNGRADEABLE';
}

describe('WHO & ICDR Clinical Decision Rules & Triage Test Suite', () => {
  it('correctly categorizes Non-Referable vs Referable DR according to WHO standards', () => {
    assert.equal(classifyReferableDR(0), false, 'Grade 0 must be Non-Referable');
    assert.equal(classifyReferableDR(1), false, 'Grade 1 must be Non-Referable');
    assert.equal(classifyReferableDR(2), true, 'Grade 2 must be Referable');
    assert.equal(classifyReferableDR(3), true, 'Grade 3 must be Referable');
    assert.equal(classifyReferableDR(4), true, 'Grade 4 must be Referable');
  });

  it('assigns appropriate clinical urgency for patient triage', () => {
    assert.equal(determineClinicalUrgency(0), 'ROUTINE');
    assert.equal(determineClinicalUrgency(1), 'ROUTINE');
    assert.equal(determineClinicalUrgency(2), 'PRIORITY');
    assert.equal(determineClinicalUrgency(3), 'URGENT');
    assert.equal(determineClinicalUrgency(4), 'EMERGENCY');
  });

  it('escalates urgency to URGENT if high macular edema (DME) risk is detected even for moderate DR', () => {
    assert.equal(determineClinicalUrgency(2, true), 'URGENT');
  });

  it('evaluates fundus image quality assurance (IQA) thresholds correctly', () => {
    assert.equal(evaluateIQAQuality(94.2), 'GRADEABLE');
    assert.equal(evaluateIQAQuality(70.0), 'GRADEABLE');
    assert.equal(evaluateIQAQuality(69.9), 'UNGRADEABLE');
    assert.equal(evaluateIQAQuality(42.1), 'UNGRADEABLE');
  });

  it('validates mock screening fixture data integrity', () => {
    const fixturePath = path.join(__dirname, 'fixtures', 'mock_clinical_data.json');
    const raw = fs.readFileSync(fixturePath, 'utf8');
    const data = JSON.parse(raw);

    assert.ok(data.hospital_node);
    assert.ok(data.district_centers.length > 0);
    assert.ok(data.patients.length > 0);
    assert.ok(data.screening_sessions.length > 0);

    const session = data.screening_sessions[0];
    assert.equal(session.status, 'VALIDATED');
    const img = session.images[0];
    assert.equal(img.ai_analysis.icdr_grade, 1);
    assert.equal(img.ai_analysis.is_referable, false);
    assert.equal(img.ai_analysis.iqa_quality, 'GRADEABLE');
  });
});
