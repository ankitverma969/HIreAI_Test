import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCandidates } from '../context/CandidateContext';
import {
  Card,
  Button,
  Loader,
  EmptyState,
  RecommendationBadge,
  CandidateScore,
  ProgressBar,
  SkillBadge
} from '../components';
import styles from './CandidateDetails.module.css';

export const CandidateDetails = () => {
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const {
    selectedCandidateDetails,
    isLoadingCandidate,
    errorCandidate,
    fetchCandidateDetails,
    clearSelectedCandidate,
  } = useCandidates();

  useEffect(() => {
    if (candidateId) {
      fetchCandidateDetails(candidateId);
    }
    return () => {
      clearSelectedCandidate();
    };
  }, [candidateId, fetchCandidateDetails]);

  if (isLoadingCandidate) {
    return <Loader text="Fetching candidate structured profile details..." />;
  }

  if (errorCandidate || !selectedCandidateDetails) {
    return (
      <EmptyState
        title="Candidate Profile Not Found"
        description="Verify the candidate ID is valid and the screening pipeline has finished."
        action={
          <Button onClick={() => navigate('/results')} variant="secondary">
            Back to Results
          </Button>
        }
      />
    );
  }

  const { profile, score, analysis } = selectedCandidateDetails;
  const breakdown = score?.breakdown || {};

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <Button variant="secondary" onClick={() => navigate('/results')} icon="◀">
          Back to Rankings
        </Button>
      </div>

      <div className={styles.container}>
        {/* Left Column: Bio & Score Breakdown */}
        <div className={styles.leftCol}>
          {/* Bio info */}
          <Card>
            <div className={styles.bioHeader}>
              <div className={styles.avatar}>
                {profile.full_name?.split(' ').map((n) => n[0]).join('').substring(0, 2) || 'CD'}
              </div>
              <div className={styles.nameBlock}>
                <h2 className={styles.name}>{profile.full_name}</h2>
                <span className={styles.roleTitle}>Software Engineering Candidate</span>
              </div>
            </div>

            <div className={styles.contactGrid}>
              {profile.email && <div className={styles.contactItem}>✉️ {profile.email}</div>}
              {profile.phone && <div className={styles.contactItem}>📞 {profile.phone}</div>}
              {profile.location && <div className={styles.contactItem}>📍 {profile.location}</div>}
              {profile.linkedin && (
                <a href={`https://${profile.linkedin}`} target="_blank" rel="noreferrer" className={styles.contactItem}>
                  🔗 LinkedIn Profile
                </a>
              )}
              {profile.github && (
                <a href={`https://${profile.github}`} target="_blank" rel="noreferrer" className={styles.contactItem}>
                  💻 GitHub Profile
                </a>
              )}
            </div>
          </Card>

          {/* Aggregate score match gauge */}
          {score && (
            <Card title="Weighted Match Breakdown">
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '20px', gap: '8px' }}>
                <CandidateScore score={score.overall_score} size={80} />
                <RecommendationBadge recommendation={analysis?.recommendation || score.reasoning} />
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                  CONFIDENCE INDEX: {score.confidence_score}%
                </span>
              </div>

              <div style={{ display: 'flex', flexParagraph: 'column', flexDirection: 'column', gap: '12px' }}>
                <ProgressBar value={breakdown.skill_match} label="Skills Alignment (35% wt)" />
                <ProgressBar value={breakdown.experience_match} label="Professional Experience (25% wt)" />
                <ProgressBar value={breakdown.project_match} label="Project Feats (15% wt)" />
                <ProgressBar value={breakdown.education_match} label="Education Match (10% wt)" />
                <ProgressBar value={breakdown.semantic_similarity} label="Semantic Similarity (10% wt)" />
                <ProgressBar value={breakdown.certification_match} label="Certifications (5% wt)" />
              </div>
            </Card>
          )}

          {/* Education list */}
          {profile.education && profile.education.length > 0 && (
            <Card title="Academic History">
              {profile.education.map((edu, idx) => (
                <div key={idx} style={{ marginBottom: idx === profile.education.length - 1 ? 0 : '16px' }}>
                  <h4 style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                    {edu.degree}
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--primary-color)', fontWeight: 600 }}>
                    {edu.university || edu.college || 'University'}
                  </p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Graduation Year: {edu.graduation_year || 'N/A'} | CGPA: {edu.cgpa || 'N/A'}
                  </p>
                </div>
              ))}
            </Card>
          )}
        </div>

        {/* Right Column: AI Analysis & Experience timeline */}
        <div className={styles.rightCol}>
          {/* AI evaluation details */}
          {analysis && (
            <Card title="AI Recruiter Evaluation Details">
              {analysis.hiring_summary && (
                <div style={{ marginBottom: '20px' }}>
                  <span className={styles.aiSectionTitle}>Summary Decision Alignment</span>
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.5, color: 'var(--text-secondary)' }}>
                    {analysis.hiring_summary}
                  </p>
                </div>
              )}

              {/* Strengths & Weaknesses */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                <div>
                  <span className={styles.aiSectionTitle}>Strengths</span>
                  <ul className={styles.bullets}>
                    {analysis.strengths?.map((str, idx) => (
                      <li key={idx} className={`${styles.bulletItem} ${styles.strengthItem}`}>
                        {str}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <span className={styles.aiSectionTitle}>Weaknesses</span>
                  <ul className={styles.bullets}>
                    {analysis.weaknesses?.map((wk, idx) => (
                      <li key={idx} className={`${styles.bulletItem} ${styles.weaknessItem}`}>
                        {wk}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Skills Overlap */}
              <div style={{ marginBottom: '20px' }}>
                <span className={styles.aiSectionTitle}>Target Technical Skills Match</span>
                <div className={styles.skillsFlex}>
                  {score?.matched_skills?.map((s) => (
                    <SkillBadge key={s} skill={s} matched={true} />
                  ))}
                  {score?.missing_skills?.map((s) => (
                    <SkillBadge key={s} skill={s} matched={false} missing={true} />
                  ))}
                </div>
              </div>

              {/* Interview questions */}
              {analysis.interview_questions && analysis.interview_questions.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <span className={styles.aiSectionTitle}>Personalized Interview Questions</span>
                  <ol className={styles.bullets} style={{ listStyle: 'decimal', paddingLeft: '16px' }}>
                    {analysis.interview_questions.map((q, idx) => (
                      <li key={idx} style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        {q}
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Study plans */}
              {analysis.learning_recommendations && analysis.learning_recommendations.length > 0 && (
                <div>
                  <span className={styles.aiSectionTitle}>Learning Recommendations</span>
                  <ul className={styles.bullets}>
                    {analysis.learning_recommendations.map((rec, idx) => (
                      <li key={idx} className={styles.bulletItem}>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          )}

          {/* Chronological work experience timeline */}
          {profile.experience && profile.experience.length > 0 && (
            <Card title="Professional Timeline">
              <div className={styles.timeline}>
                {profile.experience.map((exp, idx) => (
                  <div key={idx} className={styles.timelineItem}>
                    <div className={styles.timelineDot} />
                    <div className={styles.timelineHeader}>
                      <span className={styles.timelineRole}>{exp.role}</span>
                      <span className={styles.timelineDates}>
                        {exp.start_date} - {exp.end_date || 'Present'}
                      </span>
                    </div>
                    <p className={styles.timelineCompany}>{exp.company}</p>
                    {exp.responsibilities && (
                      <p className={styles.timelineDesc}>{exp.responsibilities}</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Projects and Feats */}
          {profile.projects && profile.projects.length > 0 && (
            <Card title="Key Projects & Systems Developed">
              {profile.projects.map((proj, idx) => (
                <div key={idx} style={{ marginBottom: idx === profile.projects.length - 1 ? 0 : '16px' }}>
                  <h4 style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                    {proj.project_name}
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.4 }}>
                    {proj.description}
                  </p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                    Technologies: {proj.technologies_used?.join(', ') || 'N/A'}
                  </p>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default CandidateDetails;
