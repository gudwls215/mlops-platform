import React from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Create, Description, Work, Mic } from '@mui/icons-material';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Mic sx={{ fontSize: 40 }} />,
      title: '음성으로 쉽게 입력',
      description: '복잡한 타이핑 없이 음성으로 경력과 경험을 말씀해 주세요. AI가 알아서 정리해 드립니다.',
      action: () => navigate('/resume/create'),
      buttonText: '음성으로 시작하기'
    },
    {
      icon: <Create sx={{ fontSize: 40 }} />,
      title: 'AI 이력서 자동 생성',
      description: '말씀해 주신 내용을 바탕으로 전문적인 이력서를 자동으로 만들어 드립니다.',
      action: () => navigate('/resume/create'),
      buttonText: '이력서 만들기'
    },
    {
      icon: <Description sx={{ fontSize: 40 }} />,
      title: '맞춤형 자기소개서',
      description: '지원하고 싶은 회사와 직무에 맞는 자기소개서를 AI가 작성해 드립니다.',
      action: () => navigate('/cover-letter'),
      buttonText: '자기소개서 작성'
    },
    {
      icon: <Work sx={{ fontSize: 40 }} />,
      title: '시니어 친화 채용정보',
      description: '50대 이상을 우대하는 채용공고를 모아서 보여드립니다.',
      action: () => navigate('/jobs'),
      buttonText: '채용정보 보기'
    }
  ];

  return (
    <Container maxWidth="lg">
      {/* 메인 히어로 섹션 */}
      <Box 
        sx={{ 
          textAlign: 'center', 
          py: { xs: 4, md: 6 },
          mb: { xs: 4, md: 6 }
        }}
      >
        <Typography 
          variant="h1" 
          component="h1" 
          gutterBottom
          sx={{ 
            fontSize: { xs: '2rem', md: '3rem' },
            fontWeight: 700,
            color: 'primary.main',
            mb: 3
          }}
        >
          시니어를 위한 똑똑한 이력서 도우미
        </Typography>
        <Typography 
          variant="h5" 
          color="text.secondary" 
          paragraph
          sx={{ 
            fontSize: { xs: '1.2rem', md: '1.5rem' },
            lineHeight: 1.6,
            maxWidth: '800px',
            mx: 'auto',
            mb: 4
          }}
        >
          음성으로 간편하게 입력하고, AI가 전문적인 이력서와 자기소개서를 만들어 드립니다.
          <br />
          50대 이상 시니어를 위한 특별한 취업 지원 서비스입니다.
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate('/resume/create')}
          sx={{ 
            fontSize: '1.2rem',
            py: 2,
            px: 4,
            minHeight: '60px'
          }}
        >
          지금 시작하기
        </Button>
      </Box>

      {/* 주요 기능 카드 */}
      <Box 
        sx={{ 
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
          gap: 4
        }}
      >
        {features.map((feature, index) => (
          <Card 
            key={index}
            sx={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4
              }
            }}
          >
            <CardContent sx={{ flexGrow: 1, textAlign: 'center', py: 4 }}>
              <Box sx={{ color: 'primary.main', mb: 2 }}>
                {feature.icon}
              </Box>
              <Typography 
                variant="h5" 
                component="h2" 
                gutterBottom
                sx={{ fontSize: '1.4rem', fontWeight: 600 }}
              >
                {feature.title}
              </Typography>
              <Typography 
                variant="body1" 
                color="text.secondary"
                sx={{ fontSize: '1.1rem', lineHeight: 1.6 }}
              >
                {feature.description}
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
              <Button
                size="large"
                variant="outlined"
                onClick={feature.action}
                sx={{ 
                  fontSize: '1rem',
                  py: 1.5,
                  px: 3,
                  minHeight: '48px'
                }}
              >
                {feature.buttonText}
              </Button>
            </CardActions>
          </Card>
        ))}
      </Box>

      {/* 추가 안내 섹션 */}
      <Box 
        sx={{ 
          textAlign: 'center', 
          py: { xs: 4, md: 6 },
          mt: { xs: 4, md: 6 },
          backgroundColor: 'grey.50',
          borderRadius: 2,
          px: 3
        }}
      >
        <Typography 
          variant="h4" 
          component="h2" 
          gutterBottom
          sx={{ fontSize: { xs: '1.5rem', md: '2rem' }, fontWeight: 600 }}
        >
          왜 시니어 이력서 도우미인가요?
        </Typography>
        <Typography 
          variant="body1" 
          sx={{ 
            fontSize: '1.1rem',
            lineHeight: 1.8,
            maxWidth: '700px',
            mx: 'auto'
          }}
        >
          오랜 경험과 노하우를 가진 시니어 여러분의 가치를 제대로 보여주는 것이 우리의 목표입니다.
          복잡한 컴퓨터 작업 없이도 음성으로 쉽게 이력서를 만들고,
          각 회사와 직무에 맞는 맞춤형 자기소개서까지 자동으로 생성해 드립니다.
        </Typography>
      </Box>
    </Container>
  );
};

export default HomePage;