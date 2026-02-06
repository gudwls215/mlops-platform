import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';
import { Description, Work, Create, Recommend, Refresh, List } from '@mui/icons-material';
import { useAppContext } from '../contexts/AppContext';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { resetAll } = useAppContext();

  const handleNewResume = () => {
    if (window.confirm('새로운 이력서를 작성하시겠습니까? 현재 진행 중인 내용이 초기화됩니다.')) {
      resetAll();
      navigate('/resume/create');
    }
  };

  return (
    <AppBar position="static" elevation={2}>
      <Toolbar sx={{ px: { xs: 2, sm: 3 } }}>
        <Typography 
          variant="h6" 
          component={Link} 
          to="/" 
          sx={{ 
            flexGrow: 1, 
            textDecoration: 'none', 
            color: 'inherit',
            fontWeight: 700,
            fontSize: '1.3rem'
          }}
        >
          시니어 이력서 도우미
        </Typography>
        
        <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 2 }}>
          {/* <Button
            color="inherit"
            startIcon={<Refresh />}
            onClick={handleNewResume}
            sx={{ 
              fontSize: '1rem', 
              px: 2,
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              }
            }}
          >
            새 이력서
          </Button> */}
          <Button
            color="inherit"
            startIcon={<Create />}
            onClick={() => navigate('/resume/create')}
            sx={{ fontSize: '1rem', px: 2 }}
          >
            이력서 작성
          </Button>
          <Button
            color="inherit"
            startIcon={<List />}
            onClick={() => navigate('/resume/list')}
            sx={{ fontSize: '1rem', px: 2 }}
          >
            내 이력서
          </Button>
          {/* <Button
            color="inherit"
            startIcon={<Description />}
            onClick={() => navigate('/cover-letter')}
            sx={{ fontSize: '1rem', px: 2 }}
          >
            자기소개서
          </Button> */}
          <Button
            color="inherit"
            startIcon={<Work />}
            onClick={() => navigate('/jobs')}
            sx={{ fontSize: '1rem', px: 2 }}
          >
            채용정보
          </Button>
          <Button
            color="inherit"
            startIcon={<Recommend />}
            onClick={() => navigate('/recommendations')}
            sx={{ fontSize: '1rem', px: 2 }}
          >
            AI 추천
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;