import React from 'react';
import { Box, Stepper, Step, StepLabel, Paper, Typography } from '@mui/material';
import { Description, Recommend, Article } from '@mui/icons-material';

interface FlowStepIndicatorProps {
  currentStep: number;
}

const steps = [
  { label: '이력서 작성', icon: <Description /> },
  { label: '채용공고 추천', icon: <Recommend /> },
  { label: '자기소개서 생성', icon: <Article /> },
];

const FlowStepIndicator: React.FC<FlowStepIndicatorProps> = ({ currentStep }) => {
  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        mb: 3,
        backgroundColor: '#f5f5f5',
      }}
    >
      <Typography
        variant="h6"
        sx={{
          mb: 2,
          textAlign: 'center',
          color: 'primary.main',
          fontWeight: 600,
        }}
      >
        진행 단계
      </Typography>
      <Stepper activeStep={currentStep - 1} alternativeLabel>
        {steps.map((step, index) => (
          <Step key={step.label}>
            <StepLabel
              StepIconComponent={() => (
                <Box
                  sx={{
                    width: 50,
                    height: 50,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor:
                      index + 1 <= currentStep
                        ? 'primary.main'
                        : 'grey.300',
                    color: 'white',
                    transition: 'all 0.3s',
                  }}
                >
                  {step.icon}
                </Box>
              )}
            >
              <Typography
                sx={{
                  mt: 1,
                  fontWeight: index + 1 === currentStep ? 700 : 400,
                  color: index + 1 <= currentStep ? 'primary.main' : 'text.secondary',
                  fontSize: '1rem',
                }}
              >
                {step.label}
              </Typography>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
    </Paper>
  );
};

export default FlowStepIndicator;
