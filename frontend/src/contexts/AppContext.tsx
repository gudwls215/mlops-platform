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
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentResume, setCurrentResume] = useState<Resume | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null);
  const [generatedCoverLetter, setGeneratedCoverLetter] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(1);

  const resetAll = () => {
    setCurrentResume(null);
    setSelectedJob(null);
    setGeneratedCoverLetter(null);
    setCurrentStep(1);
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
