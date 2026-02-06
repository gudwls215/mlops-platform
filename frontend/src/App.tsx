import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Context
import { AppProvider } from './contexts/AppContext';

// Components
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import ResumeCreatePage from './pages/ResumeCreatePage';
import ResumeListPage from './pages/ResumeListPage';
import CoverLetterPage from './pages/CoverLetterPage';
import JobListPage from './pages/JobListPage';
import LabelingPage from './pages/LabelingPage';
import HybridRecommendationPage from './pages/HybridRecommendationPage';
import FlowSummaryPage from './pages/FlowSummaryPage';

// 장년층 친화적 테마 설정
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#fafafa',
    },
  },
  typography: {
    fontSize: 16, // 기본보다 큰 폰트
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '1.1rem', // 읽기 쉬운 크기
      lineHeight: 1.6,
    },
    button: {
      fontSize: '1.1rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: '48px', // 터치하기 쉬운 크기
          padding: '12px 24px',
          borderRadius: '8px',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-input': {
            fontSize: '1.1rem',
            padding: '16px',
          },
        },
      },
    },
  },
});

function App() {
  return (
    <AppProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              minHeight: '100vh' 
            }}
          >
            <Header />
            <Box 
              component="main" 
              sx={{ 
                flexGrow: 1, 
                py: 3,
                px: { xs: 2, sm: 3 }
              }}
            >
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/resume/create" element={<ResumeCreatePage />} />
                <Route path="/resume/list" element={<ResumeListPage />} />
                <Route path="/cover-letter" element={<CoverLetterPage />} />
                <Route path="/jobs" element={<JobListPage />} />
                <Route path="/labeling" element={<LabelingPage />} />
                <Route path="/recommendations" element={<HybridRecommendationPage />} />
                <Route path="/summary" element={<FlowSummaryPage />} />
              </Routes>
            </Box>
            <Footer />
          </Box>
        </Router>
      </ThemeProvider>
    </AppProvider>
  );
}

export default App;
