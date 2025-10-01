import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#f5f5f5',
        py: 3,
        mt: 'auto',
        borderTop: '1px solid #e0e0e0'
      }}
    >
      <Container maxWidth="lg">
        <Typography 
          variant="body2" 
          color="text.secondary" 
          align="center"
          sx={{ fontSize: '1rem' }}
        >
          © 2025 시니어 이력서 도우미. 50대 이상을 위한 AI 기반 취업 지원 플랫폼
        </Typography>
        <Typography 
          variant="body2" 
          color="text.secondary" 
          align="center" 
          sx={{ mt: 1, fontSize: '0.9rem' }}
        >
          문의사항이 있으시면 언제든지 연락해 주세요.
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;