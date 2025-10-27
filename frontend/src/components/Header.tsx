import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';
import { Description, Work, Create, Recommend } from '@mui/icons-material';

const Header: React.FC = () => {
  const navigate = useNavigate();

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
            startIcon={<Description />}
            onClick={() => navigate('/cover-letter')}
            sx={{ fontSize: '1rem', px: 2 }}
          >
            자기소개서
          </Button>
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