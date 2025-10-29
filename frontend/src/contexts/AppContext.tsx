import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Resume {
  id: number;
  title: string;
  content: string;
  skills: string[];
  created_at: string;
  updated_at: string;
}

interface JobPosting {
  id: number;
  title: string;
  company: string;
  description: string;
  requirements: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
}

interface AppContextType {
  // Resume state
  currentResume: Resume | null;
  setCurrentResume: (resume: Resume | null) => void;
  
  // Job posting state
  selectedJob: JobPosting | null;
  setSelectedJob: (job: JobPosting | null) => void;
  
  // Generated cover letter state
  generatedCoverLetter: string | null;
  setGeneratedCoverLetter: (coverLetter: string | null) => void;
  
  // Flow step state
  currentStep: number;
  setCurrentStep: (step: number) => void;
  
  // Reset all state
  resetAll: () => void;
  
  // Check if flow is complete
  isFlowComplete: () => boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// LocalStorage keys
const STORAGE_KEYS = {
  RESUME: 'mlops_current_resume',
  JOB: 'mlops_selected_job',
  COVER_LETTER: 'mlops_cover_letter',
  STEP: 'mlops_current_step',
};

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initialize state from localStorage
  const [currentResume, setCurrentResumeState] = useState<Resume | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.RESUME);
    return stored ? JSON.parse(stored) : null;
  });
  
  const [selectedJob, setSelectedJobState] = useState<JobPosting | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.JOB);
    return stored ? JSON.parse(stored) : null;
  });
  
  const [generatedCoverLetter, setGeneratedCoverLetterState] = useState<string | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.COVER_LETTER);
    return stored || null;
  });
  
  const [currentStep, setCurrentStepState] = useState<number>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.STEP);
    return stored ? parseInt(stored, 10) : 1;
  });

  // Wrapper functions to save to localStorage
  const setCurrentResume = (resume: Resume | null) => {
    setCurrentResumeState(resume);
    if (resume) {
      localStorage.setItem(STORAGE_KEYS.RESUME, JSON.stringify(resume));
    } else {
      localStorage.removeItem(STORAGE_KEYS.RESUME);
    }
  };

  const setSelectedJob = (job: JobPosting | null) => {
    setSelectedJobState(job);
    if (job) {
      localStorage.setItem(STORAGE_KEYS.JOB, JSON.stringify(job));
    } else {
      localStorage.removeItem(STORAGE_KEYS.JOB);
    }
  };

  const setGeneratedCoverLetter = (coverLetter: string | null) => {
    setGeneratedCoverLetterState(coverLetter);
    if (coverLetter) {
      localStorage.setItem(STORAGE_KEYS.COVER_LETTER, coverLetter);
    } else {
      localStorage.removeItem(STORAGE_KEYS.COVER_LETTER);
    }
  };

  const setCurrentStep = (step: number) => {
    setCurrentStepState(step);
    localStorage.setItem(STORAGE_KEYS.STEP, step.toString());
  };

  const resetAll = () => {
    setCurrentResumeState(null);
    setSelectedJobState(null);
    setGeneratedCoverLetterState(null);
    setCurrentStepState(1);
    localStorage.removeItem(STORAGE_KEYS.RESUME);
    localStorage.removeItem(STORAGE_KEYS.JOB);
    localStorage.removeItem(STORAGE_KEYS.COVER_LETTER);
    localStorage.removeItem(STORAGE_KEYS.STEP);
  };

  const isFlowComplete = () => {
    return currentResume !== null && selectedJob !== null && generatedCoverLetter !== null;
  };

  return (
    <AppContext.Provider
      value={{
        currentResume,
        setCurrentResume,
        selectedJob,
        setSelectedJob,
        generatedCoverLetter,
        setGeneratedCoverLetter,
        currentStep,
        setCurrentStep,
        resetAll,
        isFlowComplete,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
